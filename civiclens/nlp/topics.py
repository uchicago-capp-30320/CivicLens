from collections import defaultdict
from typing import Callable

import numpy as np
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, PartOfSpeech
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer

from ..utils.ml_utils import clean_comments, sentence_splitter
from .tools import Comment, RepComments


# Models
POS_TAGS = [[{"POS": "ADJ"}, {"POS": "NOUN"}], [{"POS": "NOUN"}]]

REP_MODELS = {
    "KeyBert": KeyBERTInspired,
    "POS": PartOfSpeech("en_core_web_sm", pos_patterns=POS_TAGS),
}

BertModel = BERTopic(
    embedding_model=SentenceTransformer("all-mpnet-base-v2"),
    vectorizer_model=CountVectorizer(stop_words="english", ngram_range=(1, 2)),
    representation_model=REP_MODELS,
)


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


class TopicModel:
    """
    Wrapper for BERT-based topic model.
    """

    def __init__(self, model: BERTopic = BertModel):
        self.model = model
        self.topics = {}
        self.terms = {}

    def _process_sentences(self, docs: list[Comment]) -> dict[str, str]:
        """
        Map setences to comments.
        """
        sentences = {}

        for comment in docs:
            split_text = sentence_splitter(clean_comments(comment.text))
            for sentence in split_text:
                if comment.text:
                    sentences[sentence] = comment.id

        return sentences

    def run_model(self, docs: list[Comment]):
        """
        Runs model and generates topics.
        """
        sentences = self._process_sentences(docs)
        input = list(sentences.keys())

        try:
            numeric_topics, probs = self.model.fit_transform(input)
        except (ValueError, TypeError) as e:
            print(f"Hugging Face error: {e}")
            return {}

        num_topics = max(numeric_topics)

        if num_topics < 0:
            print("Too few topics generated")
            return {}

        query = self._generate_mmr_query(numeric_topics)

        # intialize no topic default
        self.topics[-1] = []
        self.terms[-1] = []

        for i in range(num_topics + 1):
            phrases = set()
            model_results = self.model.get_topic(i, full=True)
            for model_topics in model_results.values():
                phrases.update({phrase for (phrase, _) in model_topics})

            self.topics[i] = list(phrases)
            self.terms[i] = mmr_sort(list(phrases), query, lam=0.8)

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
            comment_id = sentences[input[idx]]
            topics_by_comment[comment_id][topic] = (
                topics_by_comment[comment_id].get(topic, 0) + probs[idx]
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
        if not self.topics:
            raise RuntimeError(
                "Must run topic model before generating search vector"
            )

        search_vector = set()
        for term_list in self.topics.values():
            search_vector.update(term_list)

        return list(search_vector)

    def find_n_representative_topics(
        self, labeled_comments: dict[str, int], n: int
    ) -> dict[int, list[str]]:
        """
        Generates n topic terms per comment.
        """
        # add way to make topic terms unique?
        comment_topics = {}
        for comment, topic_num in labeled_comments.items():
            terms = self.terms[topic_num]
            comment_topics[comment] = terms[:n]

        return comment_topics


class TopicChain:
    def __init__(self):
        self.promt_template = """
            Provide a label that is relevant to someone who is civically engaged
            and trying to understand regulation for this group of terms: {terms}
            """

        self.prompt = PromptTemplate.from_template(self.promt_template)
        self.pipeline = HuggingFacePipeline.from_model_id(
            model_id="google/flan-t5-base",
            task="text2text-generation",
            pipeline_kwargs={"max_length": 20},
        )
        self.chain = self.prompt | self.pipeline | StrOutputParser()

    def generate_label(self, terms: list[str]) -> list[str]:
        """
        Create better topic terms
        """
        term_string = self.chain.invoke({"terms": ", ".join(terms)})
        return term_string


def label_topics(topics: dict[int, list], model: TopicChain) -> dict[int, str]:
    """
    Generates a label for all topics

    Inputs:
        topics: dictionary of topics, as lists of terms
        model: LLM model to generate labels

    Returns:
        Dictionary of topics, and labels
    """
    labels = {}
    for topic, terms in topics.values():
        labels[topic] = model.generate_label(terms)

    return labels


def topic_comment_analysis(
    comment_data: RepComments,
    model: TopicModel = None,
    labeler: TopicChain = None,
    sentiment_analyzer: Callable = None,
) -> RepComments:
    """
    Run topic and sentiment analysis.
    """
    # cache this
    comments = comment_data.to_list()
    comment_topics = model.run_model(comments)
    # add logic for re-doing analysis here
    topic_labels = label_topics(comment_topics, labeler)

    for comment in comments:
        comment.topic_label = topic_labels[comment_topics[comment.id]]
        comment.topic = comment_topics[comment.id]
        # need fixture for this function to work
        comment.sentiment = sentiment_analyzer(comment.text)

    # create new instance of the class ?
    comment_data.rep_comments = comments
    comment_data.topics = create_topics(comments)
    comment_data.search_vector = model.generate_search_vector()

    return comment_data


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
    for topic_label, partial in temp.values():
        partial["topic"] = topic_label
        topics.append(partial)

    return topics
