from sentence_transformers import SentenceTransformer
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    T5ForConditionalGeneration,
    T5Tokenizer,
    pipeline,
)


# title models
title_model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-base")
title_tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")


# topic models
sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")

label_tokenizer = AutoTokenizer.from_pretrained(
    "fabiochiu/t5-base-tag-generation"
)
label_model = AutoModelForSeq2SeqLM.from_pretrained(
    "fabiochiu/t5-base-tag-generation"
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
