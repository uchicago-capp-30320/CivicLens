from pathlib import Path

from sentence_transformers import SentenceTransformer
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer,
    pipeline,
)


def model_path(model: str, tokenizer: bool, model_func) -> str:
    """Returns the path to a saved huggingface model and downloads the model
    if it hasn't been saved already

    Args:
        model (str): huggingface model id
        tokenizer (bool): whether the item is a tokenizer
        model_func (_type_): function used to download the item

    Returns:
        relative_path (str): relative path for accessing the model
    """
    # Define the relative path
    if tokenizer:
        relative_path = (
            Path(__file__).resolve().parent
            / "saved_models"
            / model
            / "tokenizer"
        )
    else:
        relative_path = (
            Path(__file__).resolve().parent / "saved_models" / model / "model"
        )
    # Check if the path exists
    if relative_path.exists():
        return relative_path
    else:
        model_download = model_func(model)
        model_download.save_pretrained(relative_path, from_pt=True)
        return relative_path


# title models
title_model_path = model_path(
    "google/flan-t5-base", False, T5ForConditionalGeneration.from_pretrained
)
title_model = T5ForConditionalGeneration.from_pretrained(title_model_path)
title_tokenizer_path = model_path(
    "google/flan-t5-base", True, T5Tokenizer.from_pretrained
)
title_tokenizer = T5Tokenizer.from_pretrained(title_tokenizer_path)

# TODO confirm that these models work the same way with huggingface
# topic models
sentence_path = model_path("all-MiniLM-L6-v2", False, SentenceTransformer)
sentence_transformer = SentenceTransformer(sentence_path)

label_token_path = model_path(
    "fabiochiu/t5-base-tag-generation", True, AutoTokenizer.from_pretrained
)
label_tokenizer = AutoTokenizer.from_pretrained(label_token_path)
label_model_path = model_path(
    "fabiochiu/t5-base-tag-generation",
    False,
    AutoModelForSeq2SeqLM.from_pretrained,
)
label_model = AutoModelForSeq2SeqLM.from_pretrained(label_model_path)

# sentiment models and pipeline
sentiment_model_path = model_path(
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
    False,
    AutoModelForSequenceClassification.from_pretrained,
)
sentiment_base = AutoModelForSequenceClassification.from_pretrained(
    sentiment_model_path
)
sentiment_token_path = model_path(
    "cardiffnlp/twitter-roberta-base-sentiment-latest",
    True,
    AutoTokenizer.from_pretrained,
)

sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_token_path)
tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
sentiment_pipeline = pipeline(
    "text-classification",
    model=sentiment_base,
    tokenizer=sentiment_tokenizer,
    **tokenizer_kwargs,
)
