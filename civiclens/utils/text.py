import html
import re

from django.utils.html import strip_tags


def regex_tokenize(text: str, pattern: str = r"\W+"):
    """
    Splits strings into tokens base on regular expression.

    Args:
        text: string to tokenize
        pattern: regular expression to split tokens on, defaults to white space

    Returns:
        List of strings represented tokens
    """
    return re.split(pattern, text)


def parse_html(text: str) -> str:
    """
    Encodes Regulations.gov text as UTF-8. Removes HTML entities, tags.

    Arg
        text (str): string to be cleaned

    Returns:
        Text cleaned of HTML entities and tags
    """
    utf_text = text.encode("latin1").decode("utf-8")
    return strip_tags(html.unescape(utf_text))


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
