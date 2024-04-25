import os

import networkx as nx
import polars as pl
import psycopg2
from dotenv import load_dotenv
from networkx.algorithms.community import louvain_communities
from sentence_transformers import SentenceTransformer, util


def pull_data(
    database: str,
    database_user: str,
    database_password: str,
    database_host: str,
    database_port: str,
) -> pl.DataFrame:
    try:
        connection = psycopg2.connect(
            database=database,
            user=database_user,
            password=database_password,
            host=database_host,
            port=database_port,
        )

        cursor = connection.cursor()
        # get largest group of doc comments currently in database for sample
        query = """
            SELECT id, comment
            FROM regulations_comment
            WHERE document_id = (
                SELECT document_id
                FROM regulations_comment
                GROUP BY document_id
                ORDER BY COUNT(*) DESC
                LIMIT 1
            );
                """
        cursor.execute(query)
        results = cursor.fetchall()

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

    finally:
        # Close the connection and cursor to free resources
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    df = pl.DataFrame(results, schema=["id", "comment"])

    return df


def comment_similarity(df):
    model = SentenceTransformer("all-mpnet-base-v2")
    paraphrases = util.paraphrase_mining(
        model, df["comment"].to_list(), show_progress_bar=True
    )
    # CDO heuristic is .85 as a threshold for considering comments similar
    df_paraphrases = pl.DataFrame(
        paraphrases, schema=["similarity", "idx1", "idx2"]
    ).filter(pl.col("similarity") >= 0.85)
    return df_paraphrases


def build_graph(df):
    graph_data = df.to_dicts()
    G = nx.Graph()
    # Add the edges along with their weights to the graph
    for edge in graph_data:
        G.add_edge(edge["idx1"], edge["idx2"], weight=edge["similarity"])
    return G


def get_clusters(G):
    return louvain_communities(G=G)


def assign_clusters(df, clusters):
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


def find_central_node(G, clusters):
    centrality_per_cluster = {}
    for cluster in clusters:
        subgraph = G.subgraph(cluster)
        # Using degree centrality for simplicity; you can change this metric
        centralities = nx.degree_centrality(subgraph)
        # Find the node with the highest centrality
        central_node = max(centralities, key=centralities.get)
        centrality_per_cluster[central_node] = centralities[central_node]
    return centrality_per_cluster


def representative_comments(G, clusters, df):
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
    # Load environment variables from .env file
    load_dotenv()

    # Accessing the environment variables
    database = os.getenv("DATABASE")
    database_user = os.getenv("DATABASE_USER")
    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")

    df = pull_data(
        database, database_user, database_password, database_host, database_port
    )
    df_paraphrases = comment_similarity(df)
    G = build_graph(df_paraphrases)
    clusters = get_clusters(G=G)
    # includes text, cluster, comment id for jack
    df = assign_clusters(df=df, clusters=clusters)
    print(representative_comments(G, clusters, df))
