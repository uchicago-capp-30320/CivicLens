import re

from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, PartOfSpeech
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer


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


def truncate(text: str, num_words: int) -> str:
    """
    Truncates commments:

    Inputs:
        text (str): Text of the comment
        num_words (int): Number of words to keep

    Returns:
        Truncated commented
    """
    words = text.split(" ")

    return " ".join(words[:num_words])
