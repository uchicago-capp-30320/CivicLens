import polars as pl
import regex as re
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


def clean_comments(text: str) -> str:
    """
    String cleaning function for comments.

    Inputs:
        text (str): comment text

    Returns:
        Cleaned verison of text
    """
    text = re.sub(r"<\s*br\s*/>", " ", text)
    text = re.sub(r"[^a-zA-Z0-9. -]", "", text)
    text = re.sub(r"\w*ndash\w*", "", text)

    return text


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
            # print(i, sim_ij, embeds[i], embeds[j])
            if sim_ij > max_sim_ij:
                max_sim_ij = sim_ij

        mmr = (
            lam * torch.sum(cos_sim(embeds[i], query_matrix)).item()
            - (1 - lam) * max_sim_ij
        )

        s.append((i, mmr))

    return sorted(s, key=lambda x: x[1], reverse=True)


def extract_formletters(
    df: pl.DataFrame, embeddings: torch.tensor, sim_threhold: float
):
    pass


class TopicModel:
    """'
    Class for producing topics
    """

    def __init__(self, model):
        self.model = model

    def _build_sentences(self):
        pass

    def run_model(self):
        pass

    def _generate_mmr_query(self):
        pass

    def generate_search_vector(self):
        pass

    def find_n_representative_topics(self, n):
        pass
