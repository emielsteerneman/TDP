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

query = "What material works best for the dribbler?"
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

""" Process results """
similarities_normalized = (similarities - np.min(similarities)) / (np.max(similarities) - np.min(similarities))
doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) - np.min(doc_scores))


for R in [0, 0.5, 1]:
    print(f"\n\nR = {R}")
    final_scores = R * np.array( similarities_normalized ) + (1-R) * np.array( doc_scores_normalized )

    argsort = np.argsort(final_scores)[::-1]
    for s in argsort[:10]:
        tdp_db = db_instance.get_tdp_by_id(sentences_dict[s]['tdp_id'])
        print(f"{final_scores[s]:.2f}", tdp_db.year, tdp_db.team.rjust(15), "|", sentences_dict[s]['text_raw'])