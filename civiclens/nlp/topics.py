import pickle
from collections import defaultdict
from pathlib import Path
from typing import Callable

import gensim.corpora as corpora
import numpy as np
from bertopic import BERTopic
from gensim.corpora import Dictionary
from gensim.models import HdpModel
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from civiclens.nlp.tools import Comment, RepComments
from civiclens.utils.errors import TooFewTopics, TopicModelFailure
from civiclens.utils.text import clean_text, sentence_splitter


def stopwords(model_path: Path):
    """
    Loads in pickled set of stopword for text processing.
    """
    with open(model_path, "rb") as f:
        stop_words = pickle.load(f)

    return stop_words


def mmr_sort(terms: list[str], query_string: str, lam: float) -> list[str]:
    """
    Sorts input terms by maximal marginal relevance (MMR).

    Inputs:
        terms: list of strings to sort
        query_string: query terms to compare relevance against
        lam: lambda value for MMR formula

    Returns:
        List of terms sorted by relevance to query terms
    """
    embeding_model = SentenceTransformer("all-MiniLM-L6-v2")
    term_matrix = embeding_model.encode(terms)
    query = embeding_model.encode(query_string, convert_to_numpy=True)

    indices = maximal_marginal_relevance(
        query, term_matrix, lambda_mult=lam, k=len(terms)
    )
    sorted_terms = np.array(terms)[indices]

    return sorted_terms.tolist()


class HDAModel:
    """
    Peforms LDA topic modeling
    """

    def __init__(self, tokenizer: RegexpTokenizer = None):
        self.model = None
        self.tokenizer = tokenizer
        self.stop_words = stopwords(
            Path(__file__).resolve().parent / "saved_models/stop_words.pickle"
        )
        self.lemmatizer = WordNetLemmatizer()

    def _process_text(
        self, comments: list[Comment]
    ) -> tuple[list[list[str]], dict[int, str]]:
        """
        Clean text and convert to tokens
        """
        docs = []
        document_ids = {}
        for idx, comment in enumerate(comments):
            docs.append(
                self.tokenizer.tokenize(clean_text(comment.text).lower())
            )
            document_ids[idx] = comment.id

        # remove numbers, tokens of length one, and stop words, lemmatize
        docs = [
            [
                self.lemmatizer.lemmatize(token)
                for token in doc
                if not token.isnumeric()
                and len(token) > 1
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

        # assign list of terms for
        comment_topics = {}
        for doc_id, topic in numeric_topics.items():
            comment_id = document_id[doc_id]
            topic_terms = [word for word, _ in hdp_model.show_topic(topic)]
            comment_topics[comment_id] = topic_terms

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


class TopicModel:
    """
    Wrapper for BERT-based topic model.
    """

    def __init__(self, model: BERTopic):
        self.model = model
        self.terms = {}

    def _process_sentences(self, docs: list[Comment]) -> dict[str, str]:
        """
        Map setences to comments.
        """
        sentences = defaultdict(list)

        for comment in docs:
            split_text = sentence_splitter(clean_text(comment.text))
            for sentence in split_text:
                if comment.text:
                    sentences[sentence].append(comment.id)

        return sentences

    def get_terms(self) -> dict[int, list]:
        """
        Returns generated terms for all topics
        """
        return self.terms

    def run_model(self, docs: list[Comment]):
        """
        Runs model and generates topics.
        """
        sentences = self._process_sentences(docs)
        input = list(sentences.keys())

        try:
            numeric_topics, probs = self.model.fit_transform(input)
        except Exception as error:
            raise TopicModelFailure(error) from error

        num_topics = max(numeric_topics)

        if num_topics < 0:
            raise TooFewTopics

        # intialize no topic default
        self.terms[-1] = []

        for i in range(num_topics + 1):
            phrases = set()
            model_results = self.model.get_topic(i, full=True)
            for model_topics in model_results.values():
                phrases.update({phrase for (phrase, _) in model_topics})

            self.terms[i] = list(phrases)

        return self._aggregate_comments(sentences, input, numeric_topics, probs)

    def _generate_mmr_query(self, topics):
        """
        Generates topics query to calculate MMR terms.
        """
        topic_labels = self.model.generate_topic_labels(
            nr_words=3, separator=", ", topic_prefix=False
        )
        min_topic = min(topics)

        if min_topic < 0:
            topic_labels = topic_labels[1:]

        return topic_labels

    def _aggregate_comments(
        self,
        sentences: dict[str, str],
        input: list[str],
        numeric_topics: list[int],
        probs: np.ndarray,
    ) -> dict[int, int]:
        """
        Aggregates topics from sentences to comments. If comments have multiple
        corresponding topics, topic with highest joint probability is chosen.
        """
        topics_by_comment = defaultdict(dict)
        for idx, topic in enumerate(numeric_topics):
            # turn into array and loop through to handle form letter bug
            comment_ids = sentences[input[idx]]
            for id in comment_ids:
                topics_by_comment[id][topic] = (
                    topics_by_comment[id].get(topic, 0) + probs[idx]
                )

        # find highest probability topic
        assigned_topics = {}
        for doc, topics in topics_by_comment.items():
            max_topic_prob = float("-inf")
            max_topic = -1
            for topic, prob in topics.items():
                if prob > max_topic_prob:
                    max_topic = topic
                    max_topic_prob = prob
            assigned_topics[doc] = max_topic

        return assigned_topics

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

    def find_n_representative_topics(
        self, labeled_comments: dict[str, int], n: int
    ) -> dict[int, list[str]]:
        """
        Generates n topic terms per comment.
        """
        # add way to make topic terms unique
        comment_topics = {}
        for comment, topic_num in labeled_comments.items():
            terms = self.terms[topic_num]
            comment_topics[comment] = terms[:n]

        return comment_topics


class LabelChain:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            "fabiochiu/t5-base-tag-generation"
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            "fabiochiu/t5-base-tag-generation"
        )

    def generate_label(self, terms: list[str]) -> tuple:
        """
        Create better topic terms.
        """
        text = ", ".join(terms)

        inputs = self.tokenizer(
            [text], max_length=512, truncation=True, return_tensors="pt"
        )
        output = self.model.generate(
            **inputs, num_beams=8, do_sample=True, min_length=10, max_length=64
        )

        decoded_output = self.tokenizer.batch_decode(
            output, skip_special_tokens=True
        )[0]

        return tuple(set(decoded_output.strip().split(", ")))


def label_topics(topics: dict[int, list], model: LabelChain) -> dict[int, str]:
    """
    Generates a label for all topics

    Inputs:
        topics: dictionary of topics, as lists of terms
        model: LLM model to generate labels

    Returns:
        Dictionary of topics, and labels
    """
    labels = {}
    for topic, terms in topics.items():
        labels[topic] = model.generate_label(terms)

    return labels


def topic_comment_analysis(
    comment_data: RepComments,
    model: TopicModel = None,
    labeler: LabelChain = None,
    sentiment_analyzer: Callable = None,
) -> RepComments:
    """
    Run topic and sentiment analysis.
    """
    comments: list[Comment] = []

    if comment_data.summary:
        comments += [
            Comment(text=comment_data.summary, id="Summary", source="Summary")
        ]

    comments += comment_data.to_list()
    for analysis in (
        "representative",
        "all",
    ):  # try with representative comments
        if analysis == "all":  # if failure, try with all comments
            comments += comment_data.get_nonrepresentative_comments()
        try:
            comment_topics = model.run_model(comments)
            break
        except (TooFewTopics, TopicModelFailure) as e:
            # log error
            print(e)
    else:  # return input if unable to generate comments
        return comment_data

    topic_terms = model.get_terms()
    topic_labels = label_topics(topic_terms, labeler)

    # filter out non_rep comments
    rep_comments: list[Comment] = []

    for comment in comments:
        comment.topic_label = topic_labels[comment_topics[comment.id]]
        comment.topic = comment_topics[comment.id]
        comment.sentiment = sentiment_analyzer(comment)
        if comment.representative:
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
    )


def create_topics(comments: list[Comment]) -> dict:
    """
    Condense topics for document summary
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
    for topic_label, partial in temp.items():
        partial["topic"] = topic_label
        topics.append(partial)

    # sort topics by "total"
    return sorted(topics, key=lambda topic: topic["total"], reverse=True)
