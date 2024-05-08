from datetime import datetime

import polars as pl
import torch
from pydantic import BaseModel
from sentence_transformers.util import cos_sim
from transformers import pipeline


class Comments(BaseModel, arbitrary_types_allowed=True):
    df: pl.DataFrame
    document: str = ""
    rep_comments: list[str] = []
    num_comments: int = 0
    num_unique_comments: int = 0
    num_rep_comments: int = 0
    topics: dict = {}
    created_at: datetime = datetime.today()
    _comment_list: list = []

    def __init__(self, *args, **kwargs):
        # assigns other values
        super().__init__(*args, **kwargs)
        self.num_comments = len(self.df)

    def to_list(self, field: str = "Comment"):
        """
        Returns list of comments
        """
        if not self._comment_list:
            self._comment_list = self.df[field].to_list()

        return self._comment_list

    def __len__(self):
        """
        Return number of total comments
        """
        return self.num_comments


class Comment(BaseModel):
    # probably should use id from API or
    uuid: str = ""
    text: str = ""
    comments_represented: int = 0
    representative: bool = False
    form_letter: bool = False


def comments_from_sql():
    pass


def comments_from_df(df: pl.DataFrame) -> list[Comment]:
    """
    Creates list of comments of from
    """
    pass


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


def sentiment_analysis(docs: list[str], model, tokenizer) -> list[tuple]:
    """
    Run sentiment analysis on comments.

    Inputs:
        docs: list of documents to analyze
        model: HuggingFace model for sequence classification
        tokenizer: HuggingFace tokenizer model

    Returns:
        List of tuples (text, sentiment label)
    """

    def iter_docs(docs):
        for doc in docs:
            yield doc

    tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
    pipe = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        **tokenizer_kwargs,
    )

    results = []
    for idx, out in enumerate(pipe(iter_docs(docs))):
        results.append((docs[idx], out["label"]))

    return results
