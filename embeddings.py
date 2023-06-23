import numpy as np
import matplotlib.pyplot as plt
from Database import instance as db_instance

class Embeddings:
    def __init__(self):
        print("[embeddings.py] Importing packages...")
        from sentence_transformers import SentenceTransformer

        print("Loading model...")
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

        self.dbsentences = None

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def embed(self, text):
        return self.model.encode(text)
    
    def set_sentences(self, dbsentences):
        print(f"[embeddings.py] Setting database {len(dbsentences)} sentences...")
        self.dbsentences = dbsentences
    
    def get_similar_sentences(self, sentence_embedding, n=5):
        if self.dbsentences is None:
            raise Exception("No database sentences set")

        # Embed sentence
        distances = [ [self.cosine_similarity(sentence_embedding, _['embedding']), _] for _ in self.dbsentences ]
        # Sort by distance
        distances.sort(key=lambda _: _[0], reverse=True)
        # Add distance and remove embedding
        results = [
            { 'id':sentence['id'], 'paragraph_id':sentence['paragraph_id'], 'sentence':sentence['sentence'], 'distance': float(distance) }
            for distance, sentence in distances[:20] 
        ]

        paragraph_ids = [ _['paragraph_id'] for _ in results ]

        # Count occurences of paragraph_id
        paragraph_occurences = {}
        for result in results:
            paragraph_occurences[result['paragraph_id']] = paragraph_occurences.get(result['paragraph_id'], 0) + 1
        paragraph_occurences = [ [k, v] for k, v in paragraph_occurences.items() ]
        # Sort occurences
        paragraph_occurences.sort(key=lambda _: _[1], reverse=True)
        print(paragraph_occurences)

        # Get top 3 paragraphs
        top_paragraphs = [ db_instance.get_paragraph(paragraph_id) for paragraph_id, _ in paragraph_occurences[:3] ]

        tdp_ids = list(set([ _['tdp_id'] for _ in top_paragraphs ]))
        tdps = [ db_instance.get_tdp(tdp_id) for tdp_id in tdp_ids ]

        return results, top_paragraphs, tdps

    def query(self, sentence):
        print(f"[embeddings.py] Querying '{sentence}'")
        sentence_embedding = self.embed(sentence)
        return self.get_similar_sentences(sentence_embedding)


Embeddor = Embeddings()