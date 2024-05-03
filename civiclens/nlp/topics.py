from collections import defaultdict

import numpy as np
import polars as pl
import torch
from bertopic import BERTopic
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from ..utils.ml_utils import clean_comments


def build_embeds(words: list[str]) -> dict[str, torch.tensor]:
    """
    Creates dictionary mapping list of strings to vector embedding.

    Inputs:
        words: list of words to embed

    Returns:
        Mapping of strings to text embedding
    """
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    query_matrix = embed_model.encode(words, convert_to_tensor=True)

    embeds = {}
    for idx, word in enumerate(words):
        embeds[word] = query_matrix[idx]

    return embeds


def maximal_marginal_relevance(
    words: list[str], query: str | list[str], lam: float = 0.5
) -> list[tuple[str, float]]:
    """
    Implementation of Marginal Maximal Relevance (MMR).

    Inputs:
        words: list of strings, or corpus, to extract relevant terms form
        query: list of strings or single string, query to compare corpus to
        lam: lambda value, ranging from 0 to 1, higher values create more
            diverse ranking

    Returns:
        List of tuples containg terms and MMR score, ordered from most relevant
        to least
    """
    s = []
    embeds = build_embeds(words)
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    query_matrix = embed_model.encode(query, convert_to_tensor=True)

    for i in words:
        max_sim_ij = 0

        for j, _ in s:
            sim_ij = torch.sum(cos_sim(embeds[i], embeds[j])).item()
            if sim_ij > max_sim_ij:
                max_sim_ij = sim_ij

        mmr = (
            lam * torch.sum(cos_sim(embeds[i], query_matrix)).item()
            - (1 - lam) * max_sim_ij
        )

        s.append((i, mmr))

    return sorted(s, key=lambda x: x[1], reverse=True)


def extract_formletters(
    docs: list[str],
    embeddings: torch.tensor,
    sim_threhold: float = 0.99,
) -> dict[str, int]:
    """
    Extracts from letters from collection of comments.

    Inputs:
        docs: List of comments
        embeddings: Embedding matrix for list of comments
        sim_threhold: Threhold (cosine similarity) for similar comments

    Returns:
        Dictionary containing text of identified form letters, and number
        of form comments.
    """
    df = pl.DataFrame({"comment": docs})
    df = df.with_row_index()

    form_comments = {}

    for _ in range(len(docs) // 100):
        row = df.sample(n=1)
        idx = row["index"]
        sim_tensor = cos_sim(embeddings[idx], embeddings)

        _, indices = torch.where(sim_tensor > sim_threhold)
        sample = df.filter(~df["index"].is_in(indices.tolist()))

        if (len(df) - len(sample)) / len(df) > 0.25:
            form_comments[row["comment"].item()] = len(df) - len(sample)

        df = sample

        if df.is_empty():
            break

    return form_comments


class TopicModel:
    """
    Wrapper for BERT-based topic model.
    """

    def __init__(self, model: BERTopic()):
        self.model = model
        self.topics = {}

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

        numeric_topics, probs = self.model.fit_transform(input)
        num_topics = max(numeric_topics)

        if num_topics < 0:
            raise ValueError("Unable to generate topics")

        query = self._generate_mmr_query(numeric_topics)

        self.topics[-1] = []
        for i in range(num_topics + 1):
            phrases = set()
            model_results = self.model.get_topic(i, full=True)
            for model_topics in model_results.values():
                # print(model_topics)
                phrases.update({phrase for (phrase, _) in model_topics})

            self.topics[i] = maximal_marginal_relevance(
                list(phrases), query[i], lam=0.5
            )

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
        sentences: dict[int, str],
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

    def generate_search_vector(self):
        """
        Creates array of topics to use in Django serach model.
        """
        if not self.topics:
            raise RuntimeError(
                "Must run topic model before generating search vector"
            )

        search_vector = []
        for topic in self.topics.values():
            search_vector += [term for (term, _) in topic]

        return search_vector

    def find_n_representative_topics(
        self, labeled_comments: dict[int | str, int], n: int
    ) -> dict[int, list[str]]:
        """
        Generates n topic terms per comment.
        """
        # add way to make topic terms unique?
        comment_topics = {}
        for comment, topic_num in labeled_comments.items():
            terms = self.topics[topic_num]
            comment_topics[comment] = [term for (term, _) in terms[:n]]

        return comment_topics
