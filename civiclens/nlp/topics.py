import pickle
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Callable

import gensim.corpora as corpora
from gensim.corpora import Dictionary
from gensim.models import HdpModel, Phrases
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from transformers import pipeline

from civiclens.nlp.models import title_model, title_tokenizer
from civiclens.nlp.tools import Comment, RepComments
from civiclens.utils.text import clean_text, regex_tokenize


def stopwords(model_path: Path) -> set[str]:
    """
    Loads in pickled set of stopword for text processing.

    Args:
        model_path: path from downloaded model

    Returns:
        Set of stop words.
    """
    with open(model_path, "rb") as f:
        stop_words = pickle.load(f)

    return stop_words


class HDAModel:
    """
    Peforms LDA topic modeling
    """

    def __init__(self):
        self.model = None
        self.tokenizer = partial(regex_tokenize, pattern=r"\W+")
        self.stop_words = stopwords(
            Path(__file__).resolve().parent / "saved_models/stop_words.pickle"
        )
        self.terms = None

    def _process_text(
        self, comments: list[Comment]
    ) -> tuple[list[list[str]], dict[int, str]]:
        """
        Clean text and convert to tokens
        """
        docs = []
        document_ids = {}
        for idx, comment in enumerate(comments):
            docs.append(self.tokenizer(clean_text(comment.text).lower()))
            document_ids[idx] = comment.id

        # remove numbers, 2 character tokens, and stop words
        docs = [
            [
                token
                for token in doc
                if not token.isnumeric()
                and len(token) > 2
                and token not in self.stop_words
            ]
            for doc in docs
        ]

        return docs, document_ids

    def _create_corpus(
        self, docs: list[list[str]]
    ) -> tuple[Dictionary, list[tuple]]:
        """
        Converts tokens to corpus and corresponding dictionary
        """
        bigram_generator = Phrases(docs, min_count=10).freeze()

        for doc in docs:
            for token in bigram_generator[doc]:
                if "_" in token:
                    doc.append(token)

        token_dict = corpora.Dictionary(docs)
        corpus = [token_dict.doc2bow(doc) for doc in docs]

        return token_dict, corpus

    def run_model(self, comments: list[Comment]):
        """
        Runs HDA topic analysis.
        """
        docs, document_id = self._process_text(comments)
        token_dict, corpus = self._create_corpus(docs)

        hdp_model = HdpModel(corpus, token_dict)
        numeric_topics = self._find_best_topic(hdp_model, corpus)

        comment_topics = {}
        topic_terms = {}
        for doc_id, topic in numeric_topics.items():
            comment_id = document_id[doc_id]
            if topic not in topic_terms:
                topic_terms[topic] = [
                    word for word, _ in hdp_model.show_topic(topic)
                ]
            comment_topics[comment_id] = topic

        self.terms = topic_terms

        return comment_topics

    def _find_best_topic(
        self, model: HdpModel, corpus: list[tuple]
    ) -> dict[int, int]:
        """
        Computes most probable topic per document
        """
        best_topic = {}
        for doc_id, doc in enumerate(corpus):
            max_prob = float("-inf")
            topic_id = -1
            for topic_num, prob in model[doc]:
                if prob > max_prob:
                    max_prob = prob
                    topic_id = topic_num
            best_topic[doc_id] = topic_id

        return best_topic

    def get_terms(self) -> dict:
        """
        Returns terms for a all topics
        """
        if not self.terms:
            return {}

        return self.terms

    def generate_search_vector(self) -> list[str]:
        """
        Creates array of topics to use in Django serach model.
        """
        if not self.terms:
            raise RuntimeError(
                "Must run topic model before generating search vector"
            )

        search_vector = set()
        for term_list in self.terms.values():
            search_vector.update(term_list)

        return list(search_vector)


class FlanLabeler:
    def __init__(self) -> None:
        self.summary_template = """
        You are an AI language model specialized in analyzing and summarizing
        topics from text. Your task is to generate a concise and descriptive
        topic label for a given list of words related to comments on a proposed
        federal policy. Ensure the label accurately encompasses the main theme
        represented by all the input words and relates to the provided summary
        of the legislation.

        Summary of Legislation: {summary}

        Example:
        Input words: ["healthcare", "insurance", "coverage", "affordable"]
        Summary: The proposed legislation aims to provide affordable healthcare
        by increasing insurance coverage and improving access to medical
        services for all citizens.
        Output label: "Affordable Healthcare Access"

        Now, generate a topic label for the following list of words:

        Input words: {words}
        """
        self.no_summary_template = """
        You are an AI language model specialized in analyzing and summarizing
        topics from text. Your task is to generate a concise and descriptive
        topic label for a given list of words related to comments on a proposed
        federal policy. Ensure the label accurately encompasses the main theme
        represented by all the input words.

        Example:
        Input words: ["healthcare", "insurance", "coverage", "affordable"]
        Output label: "Affordable Healthcare Access"

        Now, generate a topic label for the following list of words:

        Input words: {words}
        """
        self.model = title_model
        self.tokenizer = title_tokenizer
        self.pipe = pipeline(
            "text2text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_length=20,
        )
        self.hf_pipeline = HuggingFacePipeline(pipeline=self.pipe)
        self.parse = StrOutputParser()

    def generate_label(self, summary, terms) -> str:
        if summary:
            prompt = PromptTemplate.from_template(self.summary_template)
            chain = prompt | self.hf_pipeline | self.parse
            return chain.invoke({"summary": summary, "words": terms})

        prompt = PromptTemplate.from_template(self.no_summary_template)
        chain = prompt | self.hf_pipeline | self.parse
        return chain.invoke({"words": terms})


def label_topics(
    topics: dict[int, list], summary: str, model: FlanLabeler
) -> dict[int, str]:
    """
    Generates a label for all topics

    Args:
        topics: dictionary of topics, as lists of terms
        model: LLM model to generate labels

    Returns:
        Dictionary of topics, and labels
    """
    labels = {}
    for topic, terms in topics.items():
        labels[topic] = model.generate_label(summary, terms)

    return labels


def topic_comment_analysis(
    comment_data: RepComments,
    model: HDAModel = None,
    labeler: FlanLabeler = None,
    sentiment_analyzer: Callable = None,
) -> RepComments:
    """
    Run topic and sentiment analysis.

    Args:
        comment_data: RepComment object
        model: instance topic model class
        labeler: chain for generating topic labels
        sentiment_analyzer: function to analyze comment text sentiment

    Returns:
        RepComment object with full topic anlayis complete
    """
    comments: list[Comment] = []

    if comment_data.summary:
        comments += [
            Comment(text=comment_data.summary, id="Summary", source="Summary")
        ]

    comments += comment_data.to_list()
    if not comment_data.rep_comments:
        comment_data.representative = False
        comments += comment_data.get_nonrepresentative_comments()

    comment_topics = model.run_model(comments)
    topic_terms = model.get_terms()
    topic_labels = label_topics(topic_terms, comment_data.summary, labeler)

    # filter out non_rep comments
    rep_comments: list[Comment] = []

    for comment in comments:
        comment.topic_label = topic_labels[comment_topics[comment.id]]
        comment.topic = comment_topics[comment.id]
        comment.sentiment = sentiment_analyzer(comment)
        if comment.representative or not comment_data.representative:
            rep_comments.append(comment)

    rep_comments = sorted(
        rep_comments, key=lambda comment: comment.num_represented, reverse=True
    )

    return RepComments(
        document_id=comment_data.document_id,
        doc_comments=comment_data.doc_comments,
        rep_comments=[comment.to_dict() for comment in rep_comments],
        doc_plain_english_title=comment_data.doc_plain_english_title,
        num_total_comments=comment_data.num_total_comments,
        num_unique_comments=comment_data.num_unique_comments,
        num_representative_comment=comment_data.num_representative_comment,
        topics=create_topics(comments),
        search_vector=model.generate_search_vector(),
        representative=comment_data.representative,
    )


def create_topics(comments: list[Comment]) -> dict:
    """
    Condense topics for document summary

    Args:
        Comments: list of Comment objects

    Returns:
        Dictionary of topics, and corresponding sentiment data
    """
    temp = defaultdict(dict)

    for comment in comments:
        temp[comment.topic_label][comment.sentiment] = (
            temp[comment.topic_label].get(comment.sentiment, 0)
            + comment.num_represented
        )
        temp[comment.topic_label]["total"] = (
            temp[comment.topic_label].get("total", 0) + comment.num_represented
        )

    topics = []
    # create output dictionary
    for topic_label, part in temp.items():
        part["topic"] = topic_label
        topics.append(part)

    # sort topics by "total"
    return sorted(topics, key=lambda topic: topic["total"], reverse=True)
