from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, PartOfSpeech
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from transformers import AutoModelForSequenceClassification, AutoTokenizer


# topic models
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

# sentiment models
sentiment_model = "cardiffnlp/twitter-roberta-base-sentiment-latest"
sentiment_base = AutoModelForSequenceClassification.from_pretrained(
    sentiment_model
)
sentiment_tokenizer = AutoTokenizer.from_pretrained(sentiment_model)
