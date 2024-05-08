import networkx as nx
import polars as pl
from networkx.algorithms.community import louvain_communities
from sentence_transformers import SentenceTransformer, util

from civiclens.utils.database_access import pull_data


def get_doc_comments(schema: list[str]) -> pl.DataFrame:
    """Pulls all comments for a set of documents and preprocesses that into a
    polars dataframe

    Args:
        schema (list[str]): columns in the dataframe

    Returns:
        pl.DataFrame: formated polars df
    """ """"""
    query = """
        SELECT id, document_id, comment
        FROM regulations_comment
        WHERE document_id IN (
            SELECT DISTINCT document_id
            FROM regulations_comment
            LIMIT 5
        );
        """
    # filter out attached files
    df = pull_data(query, schema)
    pattern = (
        r"(?i)^see attached file(s)?\.?$"
        r"|(?i)^please see attached?\.?$"
        r"|(?i)^see attached?\.?"
        r"|(?i)^see attached file\(s\)\.?$"
    )

    filtered_df = df.filter(~pl.col("comment").str.contains(pattern))

    # create null column for clusters
    # (this should exist in sql eventually)
    rows = filtered_df.shape[0]
    filtered_df = filtered_df.with_columns(
        pl.Series("cluster", [None] * rows).cast(pl.Utf8)
    )
    return filtered_df


def comment_similarity(df: pl.DataFrame) -> pl.DataFrame:
    """Create df with comment mappings and their semantic similarity scores
    according to the SBERT paraphrase mining method using the all-mpnet-base-v2
    model from hugging face.

    Args:
        df (pl.DataFrame): comment data

    Returns:
        pl.DataFrame: df with pairs of comment indices and a cosine similarity
    """
    model = SentenceTransformer("all-mpnet-base-v2")
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
    df_form_letter = df_full.filter(pl.col("similarity") > 0.99)

    return df_paraphrases, df_form_letter


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
        "comment_index": [],
        "document_id": [],
        "comment_text": [],
    }
    for i, community in enumerate(clusters):
        community_size = len(community)
        central_node = list(central_nodes.keys())[i]
        representative_dict.get("comments_represented").append(community_size)
        representative_dict.get("comment_index").append(central_node)
        representative_dict.get("document_id").append(df[central_node, 1])
        representative_dict.get("comment_text").append(df[central_node, 2])

    output_df = pl.DataFrame(representative_dict)

    if form_letter:
        return output_df.unique(subset=["comment_text"])
    else:
        return output_df


if __name__ == "__main__":
    # get comments and ids for iterating through batches of document comments
    df = get_doc_comments(schema=["id", "document_id", "comment"])
    doc_ids = df["document_id"].unique()

    # go through each document and print representative comments and assign
    # clusters to the all comments in each document
    for doc in doc_ids:
        df_doc = df.filter(pl.col("document_id") == doc)
        df_paraphrases, df_form_letter = comment_similarity(df_doc)

        # we want to show form letters versus paraphrases count
        print(df_paraphrases.shape)
        print(df_doc.shape)

        try:
            G_paraphrase = build_graph(df_paraphrases)
            clusters_paraphrase = get_clusters(G=G_paraphrase)
            df_doc = assign_clusters(df=df_doc, clusters=clusters_paraphrase)
            print(
                representative_comments(
                    G_paraphrase, clusters_paraphrase, df_doc, form_letter=False
                )
            )
            print(df_doc)
        except ZeroDivisionError:
            print("Paraphrase Clustering Not Possible: Empty DataFrame")

        try:
            G_form_letter = build_graph(df_form_letter)
            clusters_form_letter = get_clusters(G=G_form_letter)
            df_doc = assign_clusters(df=df_doc, clusters=clusters_form_letter)
            print(
                representative_comments(
                    G_form_letter,
                    clusters_form_letter,
                    df_doc,
                    form_letter=True,
                )
            )
            print(df_doc)
        except ZeroDivisionError:
            print("Form Letter Clustering Not Possible: Empty DataFrame")
