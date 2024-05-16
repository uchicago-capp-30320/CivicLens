import pickle
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import polars as pl
import pytest
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

from civiclens.nlp import comments
from civiclens.nlp.models import BertModel
from civiclens.nlp.tools import Comment, RepComments
from civiclens.nlp.topics import TopicModel, mmr_sort
from civiclens.utils.errors import TopicModelFailure


BASE_DIR = Path(__file__).resolve().parent

# load real model to test error catching
live_model = TopicModel(BertModel)

sample_df = pl.read_csv(
    BASE_DIR / "nlp_test_data/sample_comments.csv", separator=","
)


def test_comment_similarity():
    df_paraphrase, df_form_letter = comments.comment_similarity(
        sample_df, model=SentenceTransformer("all-mpnet-base-v2")
    )

    assert df_paraphrase.shape == (377, 4)
    assert df_form_letter.shape == (1, 4)
    assert df_paraphrase.columns == df_paraphrase.columns
    assert df_form_letter.columns == df_form_letter.columns


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


def test_agg_comments():
    sentences = {"The dog ran": [0], "The cat ate": [0], "A big fish": [1]}
    inputs = ["The dog ran", "The cat ate", "A big fish"]
    probs = np.array([0.3, 0.8, 0.5])
    topics = [0, 1, 0]

    test_model = MagicMock(spec=BERTopic)
    topic_model = TopicModel(test_model)
    output = topic_model._aggregate_comments(sentences, inputs, topics, probs)
    assert output == {0: 1, 1: 0}


def test_agg_comments_equal_probs():
    sentences = {"The dog ran": [0], "The cat ate": [0], "A big fish": [1]}
    inputs = ["The dog ran", "The cat ate", "A big fish"]
    probs = np.array([0.3, 0.3, 0.5])
    topics = [0, 1, 0]

    test_model = MagicMock(spec=BERTopic)
    topic_model = TopicModel(test_model)
    output = topic_model._aggregate_comments(sentences, inputs, topics, probs)
    # should select first topic
    assert output == {0: 0, 1: 0}


def test_gen_search_vector():
    test_model = MagicMock(spec=BERTopic)
    topic_model = TopicModel(test_model)

    topic_model.terms = {0: ["green", "red"], 1: ["blue", "orange"]}
    # check all the values are the same
    assert set(topic_model.generate_search_vector()) == {
        "green",
        "red",
        "blue",
        "orange",
    }


def test_gen_search_unique():
    test_model = MagicMock(spec=BERTopic)
    topic_model = TopicModel(test_model)

    topic_model.terms = {0: ["green", "red"], 1: ["green", "orange"]}
    # check all values are unique
    assert len(topic_model.generate_search_vector()) == 3


def test_process_sentences():
    test_model = MagicMock(spec=BERTopic)
    topic_model = TopicModel(test_model)

    docs = [
        Comment(text="This is a comment. It has two sentences", id="0"),
        Comment(text="This is a comment with one sentence", id="1"),
    ]
    correct = {
        "This is a comment.": ["0"],
        "It has two sentences.": ["0"],
        "This is a comment with one sentence.": ["1"],
    }

    assert correct == topic_model._process_sentences(docs)


def test_catch_bertopic_errors():
    comments = RepComments(document_id="test", doc_comments=sample_df[:2])
    docs = comments.get_nonrepresentative_comments()
    with pytest.raises(TopicModelFailure):
        live_model.run_model(docs)


def test_find_2_terms():
    test_model = MagicMock(spec=BERTopic)
    topic_model = TopicModel(test_model)

    topic_model.terms = {0: ["red", "blue", "green"], 1: ["cat", "dog", "fish"]}
    labeled_comments = {0: 1, 1: 0}
    correct = {0: ["cat", "dog"], 1: ["red", "blue"]}

    assert correct == topic_model.find_n_representative_topics(
        labeled_comments, 2
    )


def test_mmr_sort():
    docs = ["cat", "fish", "sheep", "apple"]
    query = "orange"
    out = mmr_sort(docs, query, lam=0.7)

    assert out[0] == "apple"


def test_sim_clusters():
    with open(BASE_DIR / "nlp_test_data/test_embeddings.pkl", "rb") as f:
        test_data = pickle.load(f)
        mock_embeddings = test_data["embeddings"]
        out = comments.compute_similiarity_clusters(
            mock_embeddings, sim_threshold=0.05
        )
        assert out.size == 3


def test_empty_form_df():
    df = pl.DataFrame()
    mock_sbert = MagicMock(spec=SentenceTransformer)
    out_lst, num_comments = comments.find_form_letters(
        df, mock_sbert, form_threshold=10
    )
    assert out_lst == []
    assert num_comments == 0
