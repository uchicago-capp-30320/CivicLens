from collections import defaultdict

import nltk
import numpy as np
from bertopic import BERTopic
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

from ..utils.ml_utils import clean_comments


# download files for sentence tokenizer
nltk.download("punkt")


def mmr_sort(terms: list[str], query_string: str, lam: float) -> list[str]:
    """
    Sorts input terms by maximal marginal relevance
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

    def __init__(self, model: BERTopic()):
        self.model = model
        self.topics = {}
        self.terms = {}

    def _process_sentences(self, docs: list[str]) -> dict[str, int]:
        """
        Map setences to comments.
        """
        sentences = {}

        for idx, doc in enumerate(docs):
            doc_sentences = sent_tokenize(clean_comments(doc))
            for sentence in doc_sentences:
                if doc:
                    sentences[sentence] = idx

        return sentences

    def run_model(self, docs: list[str]):
        """
        Runs model and generates topics.
        """
        sentences = self._process_sentences(docs)
        input = list(sentences.keys())

        try:
            numeric_topics, probs = self.model.fit_transform(input)
        except (ValueError, TypeError):
            # log error somewhere, what to return
            return {}

        num_topics = max(numeric_topics)

        if num_topics < 0:
            # should this be an error
            raise ValueError("Unable to generate topics")

        query = self._generate_mmr_query(numeric_topics)

        # intialize no topic default
        self.topics[-1] = []
        self.terms[-1] = []

        for i in range(num_topics + 1):
            phrases = set()
            model_results = self.model.get_topic(i, full=True)
            for model_topics in model_results.values():
                # print(model_topics)
                phrases.update({phrase for (phrase, _) in model_topics})

            self.topics[i] = phrases
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
        sentences: dict[str, int],
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
        self, labeled_comments: dict[int | str, int], n: int
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
    def __init__(self, terms: list[str]):
        self.promt_template = """
        You are a term summarizer that is given a list of terms representing a
        proposed regulation. Your job is to shorten the list to four or five
        unique words that reflect the topic and is relevant to someone trying
        to comprehensively understand the regulation.

            List of terms: {terms}

            Answer:"""

        self.prompt = PromptTemplate.from_template(self.promt_template)
        self.pipeline = HuggingFacePipeline.from_model_id(
            model_id="google/flan-t5-base",
            task="text2text-generation",
            pipeline_kwargs={"max_length": 20},
        )
        self.chain = self.prompt | self.pipeline | StrOutputParser()
        self.terms = terms

    def generate_terms(self) -> list[str]:
        """
        Create better topic terms
        """
        term_string = self.chain.invoke({"terms": self.terms})
        return self._clean_terms(term_string)

    def _clean_terms(self, term_string: str) -> list[str]:
        """
        Cleans output from LLM
        """
        terms = term_string.split(",")
        unique_terms = {term.strip() for term in terms}

        return list(unique_terms)
