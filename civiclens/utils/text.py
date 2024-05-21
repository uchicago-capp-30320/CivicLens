import re
from typing import Optional


def regex_tokenize(text: str, pattern: str = r"\W+"):
    """
    Splits strings into tokens base on regular expression.

    Inputs:
        text: string to tokenize
        pattern: regular expression to split tokens on, defaults to white space

    Returns:
        List of strings represented tokens
    """
    return re.split(pattern, text)


def clean_text(text: str, patterns: Optional[list[tuple]] = None) -> str:
    r"""
    String cleaning function for comments.

    Args:
        text (str): comment text
        patterns (list[str]): optional list of regular expression patterns
            to pass in (eg. [(r'\w+', "-")])

    Returns:
        Cleaned verison of text
    """
    if patterns is None:
        patterns = []

    text = re.sub(r"<\s*br\s*/>", " ", text)
    text = re.sub(r"[^a-zA-Z0-9.'\"\?\: -]", "", text)
    text = re.sub(r"\w*ndash\w*", "", text)

    if patterns:
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)

    # remove extra whitespace
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, num_words: int) -> str:
    """
    Truncates commments:

    Args:
        text (str): Text of the comment
        num_words (int): Number of words to keep

    Returns:
        Truncated commented
    """
    words = text.split(" ")

    return " ".join(words[:num_words])


def sentence_splitter(text: str, sep: str = ".") -> list[str]:
    """
    Splits string into sentences.

    Args:
        text: string to process
        sep: value to seperate string on, defaults to '.'

    Returns:
        List of strings split on the seperator valur
    """
    # remove periods not at the end of sentences
    clean = re.sub(r"\.(?!\s)", " ", text)
    sentences = clean.split(sep)

    return [sentence.strip() + "." for sentence in sentences if sentence]
