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
    doc_comments: pl.DataFrame = Field(default=pl.DataFrame)

    # fields for nlp table
    rep_comments: list = Field(default=[])
    doc_plain_english_title: str = ""
    num_total_comments: int = 0
    num_unique_comments: int = 0
    num_representative_comment: int = 0
    topics: list = Field(default=[])
    last_updated: datetime = datetime.now()
    search_vector: list = Field(default=[])
    summary: str = ""

    # TODO tests for this method
    def get_nonrepresentative_comments(self):
        """
        Converts nonrepresentative comments to list of Comment objects.
        """
        rep_ids = set()
        for comment in self.rep_comments:
            if isinstance(comment, Comment):
                rep_ids.add(comment.id)
            else:
                rep_ids.add(comment["comment_id"])

        return [
            Comment(id=comment["id"], text=comment["comment"])
            for comment in self.doc_comments.to_dicts()
            if comment["id"] not in rep_ids
        ]

    def to_list(self):
        """
        Converts representative comments to list of Comment objects.
        """
        if not self.rep_comments:
            return []

        return [
            Comment(
                text=comment["comment_text"],
                num_represented=comment["comments_represented"],
                id=comment["comment_id"],
                form_letter=comment["form_letter"],
                representative=True,
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
    sentiment: str = ""
    source: str = "Comment"
    representative: bool = False

    def to_dict(self):
        """
        Converts comment object to dictionary.
        """
        return {
            "text": self.text,
            "num_represented": self.num_represented,
            "id": self.id,
            "topic_label": self.topic_label,
            "topic": self.topic,
            "form_letter": self.form_letter,
            "sentiment": self.sentiment,
            "source": self.source,
        }


def extract_formletters(
    docs: list[str],
    embeddings: torch.tensor,
    sim_threhold: float = 0.99,
) -> dict[str, int]:
    """
    Extracts from letters from collection of comments.

    Args:
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


def sentiment_analysis(comment: Comment, pipeline: pipeline) -> str:
    """
    Analyze sentiment of a comment.

    Args:
        comment: Comment object
        pipeline: Hugging Face pipeline for conducting sentiment analysis

    Returns:
        Sentiment label as string (e.g 'postive', 'negative', 'neutral')
    """

    out = pipeline(comment.text)[0]
    return out["label"]
