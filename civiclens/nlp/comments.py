import networkx as nx
import numpy as np
import polars as pl
from networkx.algorithms.community import louvain_communities
from sentence_transformers import SentenceTransformer, util
from sklearn.cluster import AgglomerativeClustering

from civiclens.nlp.tools import RepComments
from civiclens.utils.database_access import Database, pull_data


def get_doc_comments(id: str) -> pl.DataFrame:
    """Pulls all comments for a set of documents and preprocesses that into a
    polars dataframe

    Args:
        id (int): document id

    Returns:
        pl.DataFrame: formated polars df
    """
    query = f"""
        SELECT id, document_id, comment
        FROM regulations_comment
        WHERE document_id = '{id}';
        """  # noqa: E702, E231, E241
    # filter out attached files
    db = Database()
    df = pull_data(
        query=query, connection=db, schema=["id", "document_id", "comment"]
    )
    pattern = (
        r"(?i)^see attached file(s)?\.?$"
        r"|(?i)^please see attached?\.?$"
        r"|(?i)^see attached?\.?"
        r"|(?i)^see attached file\(s\)\.?$"
    )

    filtered_df = df.filter(~pl.col("comment").str.contains(pattern))

    # TODO create clusters column in comment table and delete these lines
    rows = filtered_df.shape[0]
    filtered_df = filtered_df.with_columns(
        pl.Series("cluster", [None] * rows).cast(pl.Utf8)
    )
    return filtered_df


def comment_similarity(
    df: pl.DataFrame, model: SentenceTransformer
) -> pl.DataFrame:
    """Create df with comment mappings and their semantic similarity scores
    according to the SBERT paraphrase mining method using the all-mpnet-base-v2
    model from hugging face.

    Args:
        df (pl.DataFrame): df with comment data
        model (SentenceTransformer): sbert sentence transformer model

    Returns:
        df_paraphrase, df_form_letter (tuple[pl.DataFrame]): cosine
            similarities for form letters and non form letters
    """
    paraphrases = util.paraphrase_mining(
        model, df["comment"].to_list(), show_progress_bar=True
    )
    df_full = pl.DataFrame(
        {
            "similarity": pl.Series(
                "similarity", [x[0] for x in paraphrases], dtype=pl.Float64
            ),
            "idx1": pl.Series(
                "idx1", [x[1] for x in paraphrases], dtype=pl.Int64
            ),
            "idx2": pl.Series(
                "idx2", [x[2] for x in paraphrases], dtype=pl.Int64
            ),
        }
    )

    df_paraphrases = df_full.filter(pl.col("similarity") <= 0.99)
    df_paraphrases = df_paraphrases.with_columns(
        pl.lit(False).alias("form_letter")
    )

    df_form_letter = df_full.filter(pl.col("similarity") > 0.99)
    df_form_letter = df_form_letter.with_columns(
        pl.lit(True).alias("form_letter")
    )

    return df_paraphrases, df_form_letter


def count_unique_comments(df: pl.DataFrame) -> int:
    """
    Counts number of unique comments identified by performing paraphrasing
    mining on a corpus of comments.

    Args:
        df: dataframe of similiar comments
    """
    indices = df["idx1"].to_list() + df["idx2"].to_list()

    return len(set(indices))


def build_graph(df: pl.DataFrame) -> nx.Graph:
    """Builds a network graph with comments as nodes and their similarities as
    weights

    Args:
        df (pl.DataFrame): df with pairs of comment indices and a cosine
            similarity

    Returns:
        nx.Graph:network graph with comments as nodes and their similarities as
            weights
    """
    graph_data = df.to_dicts()
    G = nx.Graph()
    for edge in graph_data:
        G.add_edge(edge["idx1"], edge["idx2"], weight=edge["similarity"])

    return G


def get_clusters(G: nx.Graph) -> list[set[int]]:
    """Defines clusters based on the Louvain Communities algorithm

    Args:
        G (nx.Graph): network graph with comments as nodes and their
            similarities as weights

    Returns:
        list[set[int]]: sets are clusters of comment nodes
    """
    return louvain_communities(G=G)


def assign_clusters(df: pl.DataFrame, clusters: list[set[int]]) -> pl.DataFrame:
    """Inserts cluster info into the polars df of data from the initial pull

    Args:
        df (pl.DataFrame): df from initial pull
        clusters (list[set[int]]): clusters from Louvain Communities

    Returns:
        pl.DataFrame: updated df
    """
    rows = df.shape[0]
    # go through clusters and add that info to df
    for i, cluster_data in enumerate(clusters):
        df = df.with_columns(
            pl.when(pl.arange(0, rows).is_in(cluster_data))
            .then(i)
            .otherwise(pl.col("cluster"))
            .alias("cluster")
        )

    return df


def find_central_node(G: nx.Graph, clusters: list[set[int]]) -> dict:
    """Find the most representative comment in a cluster by identifying the
    most central node

    Args:
        G (nx.Graph): network graph with comments as nodes and their
            similarities as weights
        clusters (list[set[int]]): clusters from Louvain Communities

    Returns:
        dict: dictionary with the central comment id as the key and the degree
            centrality as the value
    """
    centrality_per_cluster = {}
    for cluster in clusters:
        # focus on each specific cluster of comments
        subgraph = G.subgraph(cluster)
        # calculate the centrality of each comment in the cluster
        centralities = nx.degree_centrality(subgraph)
        # Find the node with the highest centrality
        central_node = max(centralities, key=centralities.get)
        centrality_per_cluster[central_node] = centralities[central_node]

    return centrality_per_cluster


def representative_comments(
    G: nx.Graph, clusters: list[set[int]], df: pl.DataFrame, form_letter: bool
) -> pl.DataFrame:
    """Creates a dataframe with the text of the representative comments along
    with the number of comments that are semantically represented by that text

    Args:
        G (nx.Graph): network graph with comments as nodes and their
            similarities as weights
        clusters (list[set[int]]): clusters from Louvain Communities
        df (pl.DataFrame): df from initial pull with added cluster info

    Returns:
        output_df (pl.DataFrame): df with representation information
    """
    central_nodes = find_central_node(G, clusters)
    representative_dict = {
        "comments_represented": [],
        "comment_id": [],
        "document_id": [],
        "comment_text": [],
        "form_letter": [],
    }
    for i, community in enumerate(clusters):
        community_size = len(community)
        central_node = list(central_nodes.keys())[i]
        representative_dict.get("comments_represented").append(community_size)
        representative_dict.get("comment_id").append(df[central_node, 0])
        representative_dict.get("document_id").append(df[central_node, 1])
        representative_dict.get("comment_text").append(df[central_node, 2])
        representative_dict.get("form_letter").append(form_letter)

    output_df = pl.DataFrame(representative_dict)

    if form_letter:
        return output_df.unique(subset=["comment_text"])
    else:
        return output_df


def compute_similiarity_clusters(
    embeds: np.ndarray, sim_threshold: float
) -> np.ndarray:
    """
    Extract form letters from corpus of comments.

    Args:
        embeds: array of embeddings representing the documents
        sim_threshold: distance thresholds to divide clusters

    Returns:
        Array of docs by cluster
    """
    kmeans = AgglomerativeClustering(
        n_clusters=None,
        metric="cosine",
        linkage="average",
        distance_threshold=sim_threshold,
    )
    kmeans.fit(embeds)

    return kmeans.labels_


def find_form_letters(
    df: pl.DataFrame, model: SentenceTransformer, form_threshold: int
) -> tuple[list[dict], int]:
    """
    Finds and extracts from letters by clustering, counts number of unique
    comments.

    Args:
        df: dataframe of comments to extract form letters from
        model: vectorize model for text embeddings
        form_threshold: threshold to consider a comment a form letter

    Returns:
        List of form letters, number of unique comments
    """
    # TODO clean strings
    num_form_letters = 0
    form_letters = []
    docs = df["comment_text"].to_numpy()

    if len(docs) <= 1:  # cannot cluster with less than 2 documents
        return form_letters, num_form_letters

    embeds = model.encode(docs, convert_to_numpy=True)
    clusters = compute_similiarity_clusters(embeds, sim_threshold=0.025)
    document_id = df.unique(subset="document_id").select("document_id").item()

    num_form_letters += clusters.max() + 1
    for cluster in range(num_form_letters):
        cluster_docs = docs[np.where(clusters == cluster)]
        if cluster_docs.size == 0:
            continue

        num_rep = (
            df.filter(pl.col("comment_text").is_in(cluster_docs))
            .select("comments_represented")
            .sum()
            .item()
        )
        letter_text = np.random.choice(cluster_docs, size=1).item()
        letter_id = (
            df.filter(pl.col("comment_text") == letter_text)
            .select("comment_id")
            .item()
        )

        form_letter = True
        if num_rep <= form_threshold:
            form_letter = False

        form_letters.append(
            {
                "comments_represented": num_rep,
                "comment_id": letter_id,
                "document_id": document_id,
                "comment_text": letter_text,
                "form_letter": form_letter,
            }
        )

    return form_letters, num_form_letters


def rep_comment_analysis(id: str, model: SentenceTransformer) -> RepComments:
    """Runs all representative comment code for a document

    Args:
        id (str): document id for comment analysis

    Returns:
        RepComment: dataclass with comment data
    """
    df = get_doc_comments(id=id)
    df_paraphrases, df_form_letter = comment_similarity(df, model)

    try:
        G_paraphrase = build_graph(df_paraphrases)
        clusters_paraphrase = get_clusters(G=G_paraphrase)
        df = assign_clusters(df=df, clusters=clusters_paraphrase)
        df_rep_paraphrase = representative_comments(
            G_paraphrase, clusters_paraphrase, df, form_letter=False
        ).sort(pl.col("comments_represented"), descending=True)
    except ZeroDivisionError:
        print("Paraphrase Clustering Not Possible: Empty DataFrame")

    try:
        G_form_letter = build_graph(df_form_letter)
        clusters_form_letter = get_clusters(G=G_form_letter)
        df = assign_clusters(df=df, clusters=clusters_form_letter)
        df_rep_form = representative_comments(
            G_form_letter,
            clusters_form_letter,
            df,
            form_letter=True,
        ).sort(pl.col("comments_represented"), descending=True)
    except ZeroDivisionError:
        print("Form Letter Clustering Not Possible: Empty DataFrame")

    # fill out comment class
    comment_data = RepComments(document_id=id, doc_comments=df)
    form_letters, num_form_letters = find_form_letters(
        df_rep_form, model, form_threshold=10
    )

    if df_rep_form.is_empty():
        comment_data.rep_comments = df_rep_paraphrase.to_dicts()
        comment_data.num_representative_comment = df_rep_paraphrase.shape[0]
    elif df_rep_paraphrase.is_empty():
        comment_data.rep_comments = form_letters
        comment_data.num_representative_comment = num_form_letters
    else:
        comment_data.rep_comments = form_letters + df_rep_paraphrase.to_dicts()
        comment_data.num_representative_comment = len(comment_data.rep_comments)

    num_paraphrased = count_unique_comments(df_paraphrases)
    comment_data.num_total_comments = df.shape[0]
    comment_data.num_unique_comments = (
        num_paraphrased + num_form_letters
        if num_paraphrased < comment_data.num_total_comments
        else num_paraphrased
    )

    return comment_data
