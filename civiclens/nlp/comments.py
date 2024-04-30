import networkx as nx
import polars as pl
from networkx.algorithms.community import louvain_communities
from sentence_transformers import SentenceTransformer, util

from ..utils.database_access import pull_data


def get_doc_comments(schema: list[str]) -> pl.DataFrame:
    query = """
        SELECT id, document_id, comment
        FROM regulations_comment
        WHERE document_id IN (
            SELECT DISTINCT document_id
            FROM regulations_comment
            LIMIT 5
        );
        """
    return pull_data(query, schema)


def comment_similarity(df: pl.DataFrame) -> pl.DataFrame:
    """Create df with comment mappings and their semantic similarity scores
    according to the SBERT paraphrase mining mthid using the all-mpnet-base-v2
    model from hugging face. A minimum similarity of .85 is used for inclusion
    following the methodology of this CDO report:
    https://www.cdo.gov/news/public-comment-analysis-pilot/

    Args:
        df (pl.DataFrame): comment data

    Returns:
        pl.DataFrame: df with pairs of comment indices and a cosine similarity
    """
    model = SentenceTransformer("all-mpnet-base-v2")
    paraphrases = util.paraphrase_mining(
        model, df["comment"].to_list(), show_progress_bar=True
    )
    df_paraphrases = pl.DataFrame(
        paraphrases, schema=["similarity", "idx1", "idx2"]
    ).filter(pl.col("similarity") <= 0.99)

    df_form_letter = pl.DataFrame(
        paraphrases, schema=["similarity", "idx1", "idx2"]
    ).filter(pl.col("similarity") > 0.99)

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
    # create null column for clusters (this should exist in sql eventually)
    rows = df.shape[0]
    df = df.with_columns(pl.Series("cluster", [None] * rows).cast(pl.Utf8))

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
    G: nx.Graph, clusters: list[set[int]], df: pl.DataFrame
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
        "comment_text": [],
    }
    for i, community in enumerate(clusters):
        community_size = len(community)
        central_node = list(central_nodes.keys())[i]
        representative_dict.get("comments_represented").append(community_size)
        representative_dict.get("comment_id").append(central_node)
        representative_dict.get("comment_text").append(df[central_node, 1])

    output_df = pl.DataFrame(representative_dict)

    return output_df


if __name__ == "__main__":
    df = get_doc_comments()

    # get semantic similarities of comments
    df_paraphrases, df_form_letter = comment_similarity(df)

    # build graph to represent significant similarity relationships
    G_paraphrase = build_graph(df_paraphrases)
    G_form = build_graph(df_form_letter)

    # cluster top relationships to add another filter for relationship quality
    clusters_paraphrase = get_clusters(G=G_paraphrase)
    clusters_form = get_clusters(G=G_form)

    # includes text, cluster, comment id
    df_clusters = assign_clusters(df=df, clusters=clusters_paraphrase)
    # df_form = assign_clusters(df=df, clusters=clusters_form)

    # print out current format of output
    print("Paraphrases:")
    print(representative_comments(G_paraphrase, clusters_paraphrase, df))
    print("Form Letters:")
    print(representative_comments(G_form, clusters_form, df))
    print("-----------")
    print(df_clusters.head())
