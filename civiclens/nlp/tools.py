from datetime import datetime
from uuid import uuid4

import polars as pl
import torch
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from sentence_transformers.util import cos_sim
from transformers import pipeline


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class RepComments:
    # clustered df for topics
    document_id: str
    doc_comments: pl.DataFrame = Field(default=pl.DataFrame())

    # fields for nlp table
    rep_comments: list = Field(default=list)
    doc_plain_english_title: str = ""
    num_total_comments: int = 0
    num_unique_comments: int = 0
    num_representative_comment: int = 0
    topics: list = Field(default=list)
    last_updated: datetime = datetime.now()
    uuid: int = uuid4().int

    def to_list(self):
        """
        Converts RepComments to list of Comment objects
        """
        if not self.rep_comments:
            return []

        return [
            Comment(
                text=comment["text"],
                num_represented=comment["comments_represented"],
                id=["commnent_id"],
                form_letter=comment["form_letter"],
            )
            for comment in self.rep_comments
        ]


@dataclass
class Comment:
    text: str = ""
    num_represented: int = 1
    id: str = str(uuid4())
    topic_label: str = ""
    topic: list[str] = None
    form_letter: bool = False


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


def sentiment_analysis(
    comments: list[Comment], model, tokenizer
) -> list[tuple]:
    """
    Run sentiment analysis on comments.

    Inputs:
        docs: list of documents to analyze
        model: HuggingFace model for sequence classification
        tokenizer: HuggingFace tokenizer model

    Returns:
        List of tuples (text, sentiment label)
    """

    def iter_comments(comments: list[Comment]):
        for comment in comments:
            yield comment.text

    tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
    pipe = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        **tokenizer_kwargs,
    )

    results = []
    for idx, out in enumerate(pipe(iter_comments(comments))):
        results.append((comments[idx], out["label"]))

    return results
