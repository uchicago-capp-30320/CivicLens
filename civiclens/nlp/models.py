from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)


# sentiment models
sentiment_model = "cardiffnlp/twitter-roberta-base-sentiment-latest"
sentiment_base = AutoModelForSequenceClassification.from_pretrained(
    sentiment_model
)
sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_model)
tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}

sentiment_pipeline = pipeline(
    "text-classification",
    model=sentiment_base,
    tokenizer=sentiment_tokenizer,
    **tokenizer_kwargs,
)
