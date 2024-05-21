import pickle
from pathlib import Path
from unittest.mock import MagicMock

import polars as pl

from civiclens.nlp import comments
from civiclens.nlp.models import sentence_transformer
from civiclens.nlp.tools import Comment
from civiclens.nlp.topics import HDAModel


BASE_DIR = Path(__file__).resolve().parent

# load real model to test error catching

sample_df = pl.read_csv(
    BASE_DIR / "nlp_test_data/sample_comments.csv", separator=","
)


def test_comment_similarity():
    df_paraphrase, df_form_letter = comments.comment_similarity(
        sample_df, model=sentence_transformer
    )
    cols = ["similarity", "idx1", "idx2", "form_letter"]
    assert df_paraphrase.columns == cols
    assert df_form_letter.columns == cols


def test_graph():
    df_paraphrase = pl.read_csv(
        BASE_DIR / "nlp_test_data/df_paraphrase.csv", separator=","
    )

    # build graph
    G = comments.build_graph(df_paraphrase)

    # cluster graph
    clusters = comments.get_clusters(G=G)
    assert isinstance(clusters, list), "Clusters is not a list"
    for cluster in clusters:
        assert isinstance(cluster, set), "Cluster is not a set"


def test_cluster_assignment():
    # read in correct df with clustered comments
    df_cluster = pl.read_csv(
        BASE_DIR / "nlp_test_data/sample_comments_cluster.csv",
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


def test_gen_search_vector():
    topic_model = HDAModel()

    topic_model.terms = {0: ["green", "red"], 1: ["blue", "orange"]}
    # check all the values are the same
    assert set(topic_model.generate_search_vector()) == {
        "green",
        "red",
        "blue",
        "orange",
    }


def test_hda_remove_num():
    topic_model = HDAModel()
    test_comment = [Comment(text="twelve 12", id="123")]
    words, _ = topic_model._process_text(test_comment)
    assert words == [["twelve"]]


def test_hda_stop_words():
    topic_model = HDAModel()
    test_comment = [Comment(text="the dog is black", id="123")]
    words, _ = topic_model._process_text(test_comment)
    assert words == [["dog", "black"]]


def test_gen_search_unique():
    topic_model = HDAModel()

    topic_model.terms = {0: ["green", "red"], 1: ["green", "orange"]}
    # check all values are unique
    assert len(topic_model.generate_search_vector()) == 3


def test_sim_clusters():
    with open(BASE_DIR / "nlp_test_data/test_embeddings.pkl", "rb") as f:
        test_data = pickle.load(f)
        mock_embeddings = test_data["embeddings"]
        out = comments.compute_similiarity_clusters(
            mock_embeddings, sim_threshold=0.05
        )
        assert out.size == 3


def test_empty_form_df():
    df = pl.DataFrame({"comment_text": []})
    mock_sbert = MagicMock(spec=sentence_transformer)
    out_lst, num_comments = comments.find_form_letters(
        df, mock_sbert, form_threshold=10
    )
    assert out_lst == []
    assert num_comments == 0
