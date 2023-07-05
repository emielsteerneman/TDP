from rank_bm25 import BM25Okapi
import Database
from Database import instance as db_instance
import time 
import numpy as np
from embeddings import Embeddor as E

import nltk
# nltk.download('stopwords')
from nltk.corpus import stopwords
sw_nltk = stopwords.words('english')

# Get all sentences from database
now = time.time()
sentences_dict = db_instance.get_sentences_exhaustive()

# Tokenize sentences
now = time.time()
tokenized_corpus = [_['text'].split(" ") for _ in sentences_dict]
bm25 = BM25Okapi(tokenized_corpus)
print(f"Time taken to create BM25 model: {time.time() - now:.2f} seconds")

# sentences_db = [ Database.Sentence_db.from_dict(_) for _ in sentences_dict ]
# E.set_sentences(sentences_db)

query = "I want to know more about ROS and how it works"
query_clean = " ".join([ word for word in query.lower().split(' ') if word not in sw_nltk ])

print(f"[bm25]       query: {query}")
print(f"[bm25] clean query: {query_clean}")

query_vector = E.embed(query_clean)

""" Get vector similarities """
now = time.time()
similarities = np.array([ E.cosine_similarity(query_vector, sentence['embedding']) for sentence in sentences_dict ])
print(f"Time taken to get {len(similarities)} similarities: {time.time() - now:.2f} seconds")

""" Get doc scores """
tokenized_query = [ word for word in query.lower().split(' ') if word not in sw_nltk ]
now = time.time()
doc_scores = bm25.get_scores(tokenized_query)
print(f"Time taken to get {len(doc_scores)} scores: {time.time() - now:.2f} seconds")

print(similarities[:3])
print()
print(doc_scores[:3])

# Get indices of top three similarites
argsort = np.argsort(similarities)[::-1][:3]
print(similarities[argsort])
for i in argsort:
    print(sentences_dict[i]['text_raw'])

print("\n------\n")

# Get indices of top three doc scores
argsort = np.argsort(doc_scores)[::-1][:3]
print(doc_scores[argsort])
for i in argsort:
    print(sentences_dict[i]['text_raw'])

exit()

""" Process results """
distances, sentences_db = list(zip(*distances_sentencesdb))
distances_normalized = (distances - np.min(distances)) / (np.max(distances) - np.min(distances))
doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) - np.min(doc_scores))

print(doc_scores)

R = 0
final_scores = R * np.array( distances_normalized ) + (1-R) * np.array( doc_scores_normalized )

print(f"Highest score: {np.max(final_scores)}")

argsort = np.argsort(final_scores)[::-1]

for s in argsort[:10]:
    print(f"{final_scores[s]:.2f}", sentences_dict[s]['year'], sentences_dict[s]['team'].rjust(15), "|", sentences_dict[s]['text'])


# wer = 0
# for i_score, score in enumerate(final_scores):
#     # print(score)
#     if 4 < score:
#         wer += 1
#         print(score, "|", sentences_dict[i_score]['text'])

# print(wer)
# print(len([ _ for _ in sentences_dict if "grsim" in _['text']]))

# argsort = np.argsort(doc_scores)[::-1]
# for i in range(5):
#     print(sentences_dict[argsort[i]]['text'])

# now = time.time()
# topk = bm25.get_top_n(tokenized_query, tokenized_corpus, n=5)
# print(f"Time taken to get scores: {time.time() - now:.2f} seconds")
# print(topk)