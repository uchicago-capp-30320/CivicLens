from pathlib import Path

from sentence_transformers import SentenceTransformer
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer,
    pipeline,
)


def model_path(model: str, tokenizer: bool, sbert: bool, model_func) -> str:
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
    # if model isn't saved, download it and return its path
    if relative_path.exists():
        return str(relative_path)
    else:
        if sbert:
            print(relative_path, type(relative_path))
            model_download = model_func(model_name_or_path=model)
            model_download.save(path=str(relative_path))
        else:
            model_download = model_func(model)
            model_download.save_pretrained(relative_path, from_pt=True)
        return str(relative_path)


# title models
title_model_path = model_path(
    model="google/flan-t5-base",
    tokenizer=False,
    sbert=False,
    model_func=T5ForConditionalGeneration.from_pretrained,
)
title_model = T5ForConditionalGeneration.from_pretrained(title_model_path)
title_tokenizer_path = model_path(
    model="google/flan-t5-base",
    tokenizer=True,
    sbert=False,
    model_func=T5Tokenizer.from_pretrained,
)
title_tokenizer = T5Tokenizer.from_pretrained(title_tokenizer_path)

# topic models
sentence_transformer_path = model_path(
    model="all-MiniLM-L6-v2",
    tokenizer=False,
    sbert=True,
    model_func=SentenceTransformer,
)
sentence_transformer = SentenceTransformer(sentence_transformer_path)


# sentiment models and pipeline
sentiment_model_path = model_path(
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    tokenizer=False,
    sbert=False,
    model_func=AutoModelForSequenceClassification.from_pretrained,
)
sentiment_base = AutoModelForSequenceClassification.from_pretrained(
    sentiment_model_path
)
sentiment_token_path = model_path(
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    tokenizer=True,
    sbert=False,
    model_func=AutoTokenizer.from_pretrained,
)

sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_token_path)
tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
sentiment_pipeline = pipeline(
    "text-classification",
    model=sentiment_base,
    tokenizer=sentiment_tokenizer,
    **tokenizer_kwargs,
)
