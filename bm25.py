from rank_bm25 import BM25Okapi
from Database import instance as db_instance
import time 
import numpy as np
from embeddings import Embeddor as E

# Get all sentences from database
now = time.time()
sentences_db = db_instance.get_sentences(inclusive=True)

# Tokenize sentences
now = time.time()
tokenized_corpus = [_['sentence'].split(" ") for _ in sentences_db]
bm25 = BM25Okapi(tokenized_corpus)
print(f"Time taken to create BM25 model: {time.time() - now:.2f} seconds")

E.set_sentences(sentences_db)

query = "I want to know more about ROS and how it works"
query = "ros"

now = time.time()
distances = [ _[0] for _ in E.query(query) ]
print(f"Time taken to get distances: {time.time() - now:.2f} seconds")

print(len(distances))

tokenized_query = query.lower().split(" ")

now = time.time()
doc_scores = bm25.get_scores(tokenized_query)
print(f"Time taken to get scores: {time.time() - now:.2f} seconds")

print(len(doc_scores))
# exit()

# print(distances[:10])
# print(doc_scores[:10])
# exit()

distances_normalized = (distances - np.min(distances)) / (np.max(distances) - np.min(distances))
doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) - np.min(doc_scores))

R = 0
final_scores = R * np.array( distances_normalized ) + (1-R) * np.array( doc_scores_normalized )

print(f"Highest score: {np.max(final_scores)}")

argsort = np.argsort(final_scores)[::-1]

for s in argsort[:10]:
    print(f"{final_scores[s]:.2f}", sentences_db[s]['year'], sentences_db[s]['team'].rjust(15), "|", sentences_db[s]['sentence'])


# wer = 0
# for i_score, score in enumerate(final_scores):
#     # print(score)
#     if 4 < score:
#         wer += 1
#         print(score, "|", sentences_db[i_score]['sentence'])

# print(wer)
# print(len([ _ for _ in sentences_db if "grsim" in _['sentence']]))

# argsort = np.argsort(doc_scores)[::-1]
# for i in range(5):
#     print(sentences_db[argsort[i]]['sentence'])

# now = time.time()
# topk = bm25.get_top_n(tokenized_query, tokenized_corpus, n=5)
# print(f"Time taken to get scores: {time.time() - now:.2f} seconds")
# print(topk)