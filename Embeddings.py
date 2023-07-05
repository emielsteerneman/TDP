import numpy as np
import Database
from Database import instance as db_instance

import nltk
# nltk.download('stopwords')
from nltk.corpus import stopwords
sw_nltk = stopwords.words('english')

class Embeddings:
    def __init__(self):
        print("[embeddings.py] Importing packages...")
        from sentence_transformers import SentenceTransformer

        print("[embeddings.py] Loading model 'sentence-transformers/all-mpnet-base-v2'...")
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

        self.dbsentences:list[Database.Sentence_db] = None

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def embed(self, text):
        return self.model.encode(text)
    
    def set_sentences(self, dbsentences):
        print(f"[embeddings.py] Setting database {len(dbsentences)} sentences...")
        self.dbsentences = dbsentences
    
    def get_similar_sentences(self, query_embedding:np.array, n=5) -> tuple[list[Database.Sentence_db], list[Database.Paragraph_db], list[Database.TDP_db]]:
        if self.dbsentences is None:
            raise Exception("No database sentences set")

        # Get distance to all other sentence embeddings
        distances = [ [self.cosine_similarity(query_embedding, sentence_db.embedding), sentence_db ] for sentence_db in self.dbsentences ]
        # Sort by distance
        distances.sort(key=lambda _: _[0], reverse=True)
        distances = distances[:20]
        # Add distance to sentences
        results = [{ 'sentence':sentence_db, 'distance': float(distance) } for distance, sentence_db in distances ]

        # Retrieve all paragraph ids from all selected sentences
        paragraph_ids = [ _['sentence'].paragraph_id for _ in results ]
        # Count occurences of paragraph_id
        paragraph_occurences = {}
        for paragraph_id in paragraph_ids:
            paragraph_occurences[paragraph_id] = paragraph_occurences.get(paragraph_id, 0) + 1
        paragraph_occurences = [ [k, v] for k, v in paragraph_occurences.items() ]
        # Sort occurences
        paragraph_occurences.sort(key=lambda _: _[1], reverse=True)
        print("[embeddings.py][gss] paragraph_occurences", paragraph_occurences)

        # Get all paragraphs
        paragraphs = [ db_instance.get_paragraph_by_id(paragraph_id) for paragraph_id, _ in paragraph_occurences ]
        # Get top 3 paragraphs
        top_paragraphs = paragraphs[:3]
        
        tdp_ids = list(set([ _.tdp_id for _ in paragraphs ]))
        tdps = [ db_instance.get_tdp_by_id(tdp_id) for tdp_id in tdp_ids ]

        sentences = [ _['sentence'] for _ in results ]

        return sentences, top_paragraphs, tdps

    def query(self, sentence_:str):
        sentence = sentence_
        print(f"[embeddings.py] Querying '{sentence}'")
        words = [ word for word in sentence.lower().split(' ') if word not in sw_nltk ]
        sentence = " ".join(words)
        print(f"[embeddings.py] Cleaned up '{sentence}'")
        query_embedding = self.embed(sentence)
        return *self.get_similar_sentences(query_embedding), sentence_, words


Embeddor = Embeddings()