
import json
from bertopic import BERTopic
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance, TextGeneration
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN
from nltk.tokenize import sent_tokenize, word_tokenize


summary = "This proposed rule would amend the regulations for certain HUD Public and Indian Housing and Housing Programs. The proposed amendments would revise existing regulations that govern admission for applicants with criminal records or a history of involvement with the criminal justice system and eviction or termination of assistance of persons on the basis of illegal drug use, drug-related criminal activity, or other criminal activity. The proposed revisions would require that prior to any discretionary denial or termination for criminal activity, PHAs and assisted housing owners take into consideration multiple sources of information, including but not limited to the recency and relevance of prior criminal activity. They are intended to minimize unnecessary exclusions from these programs while allowing providers to maintain the health, safety, and peaceful enjoyment of their residents, their staffs, and their communities. The proposed rule is intended to both clarify existing PHA and owner obligations and reduce the risk of violation of nondiscrimination laws."

with open("../HUD-2024-0031-0001_comments.json", "r") as f:
    comments = json.loads(f.read())

comment_text = []

for comment in comments:
    comment_text.append(comment['data']['attributes']['comment'])

# remove empty comment
docs = [comment for comment in comment_text if comment]
sentences = [sent_tokenize(comment) for comment in docs]
sentences = [sentence for doc in sentences for sentence in doc]

# hdbscan_model = HDBSCAN(min_cluster_size=150, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
vectorizer_model = CountVectorizer(stop_words="english", min_df=2, ngram_range=(1, 2))

keybert_model = KeyBERTInspired()
# # MMR
# mmr_model = MaximalMarginalRelevance(diversity=0.3)

tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

prompt = f"""
Here is a proposed rule change from the federal government: {summary}
The following documents represent public comments on this rule: [DOCUMENTS] 
Topics from these documents are described by the following keywords: [KEYWORDS]

Based on the above information, create a breif, 2 to 3 word, label for each topic.
"""
tokenizer_kwargs = {'truncation': True, 'max_length': 512}

generator = pipeline('text2text-generation', tokenizer=tokenizer, model=model, **tokenizer_kwargs)
flan_model = TextGeneration(generator, prompt=prompt, nr_docs=12)

models = {
    "KeyBERT": keybert_model,
    # "MMR": mmr_model,
    "Flan": flan_model
}

topic_model = BERTopic(vectorizer_model=vectorizer_model, representation_model=models)
topics, probs = topic_model.fit_transform(sentences)

print(topic_model.get_topic_info()['Flan'])





