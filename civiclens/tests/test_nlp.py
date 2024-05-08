import networkx as nx
import polars as pl

from civiclens.nlp import comments


def test_comment_similarity():
    df = pl.read_csv(
        "civiclens/tests/nlp_test_data/sample_comments.csv", separator=","
    )
    df_paraphrase, df_form_letter = comments.comment_similarity(df)

    assert df_paraphrase.shape == (377, 3)
    assert df_form_letter.shape == (1, 3)
    assert df_paraphrase.columns == df_paraphrase.columns
    assert df_form_letter.columns == df_form_letter.columns


def test_graph():
    df_paraphrase = pl.read_csv(
        "civiclens/tests/nlp_test_data/df_paraphrase.csv", separator=","
    )

    # build graph
    G = comments.build_graph(df_paraphrase)
    nx.draw(G)

    # cluster graph
    clusters = comments.get_clusters(G=G)
    assert isinstance(clusters, list), "Clusters is not a list"
    for cluster in clusters:
        assert isinstance(cluster, set), "Cluster is not a set"


def test_cluster_assignment():
    # read in correct df with clustered comments
    df_cluster = pl.read_csv(
        "civiclens/tests/nlp_test_data/sample_comments_cluster.csv",
        separator=",",
    )

    # remove cluster assignments
    df = df_cluster.with_columns(pl.lit(None).alias("cluster"))
    clusters = [
        {0, 1, 2, 4, 6, 7, 8, 9, 11, 12, 13, 17, 18, 23},
        {3, 5, 10, 14, 15, 16, 19, 20, 21, 22, 24, 25, 26, 27},
    ]

    # assign clusters and confirm the algorithm is consistent
    df = comments.assign_clusters(df=df, clusters=clusters)
    assert df_cluster.equals(df)
