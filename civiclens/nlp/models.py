from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, PartOfSpeech
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)


# topic models
pos_tags = [[{"POS": "ADJ"}, {"POS": "NOUN"}], [{"POS": "NOUN"}]]

rep_models = {
    "KeyBert": KeyBERTInspired,
    "POS": PartOfSpeech("en_core_web_sm", pos_patterns=pos_tags),
}

BertModel = BERTopic(
    embedding_model=SentenceTransformer("all-mpnet-base-v2"),
    vectorizer_model=CountVectorizer(stop_words="english", ngram_range=(1, 2)),
    representation_model=rep_models,
)

# sentiment models
sentiment_model = "cardiffnlp/twitter-roberta-base-sentiment-latest"
sentiment_base = AutoModelForSequenceClassification.from_pretrained(sentiment_model)
sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_model)
tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}

sentiment_pipeline = pipeline(
    "text-classification",
    model=sentiment_base,
    tokenizer=sentiment_tokenizer,
    **tokenizer_kwargs,
)
