import numpy as np
from openai import OpenAI

from MyLogger import logger

class Embeddor:
    def __init__(self):
        self.model = None
        self.openai_client = None

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def embed_using_sentence_transformer(self, text:str | list[str]) -> np.array:
        if self.model is None:
            self.load_sentence_transformer()
        return self.model.encode(text)

    def embed_using_openai(self, text:str | list[str], model="text-embedding-3-small") -> np.array:
        if self.openai_client is None:
            self.load_openai_client()
        
        is_str:bool = type(text) == str

        if is_str: 
            response = self.openai_client.embeddings.create(input = [text], model=model)
            return np.array(response.data[0].embedding)
        else:
            response = self.openai_client.embeddings.create(input = text, model=model)
            return np.array([ _.embedding for _ in response.data ])

    def load_sentence_transformer(self) -> None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading model 'sentence-transformers/all-mpnet-base-v2'")
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        logger.info("Model loaded")
    
    def load_openai_client(self) -> None:
        self.openai_client = OpenAI()
        logger.info("OpenAI client loaded")
    
    # def get_similar_sentences(self, query_embedding:np.array, n=5) -> tuple[list[Database.Sentence_db], list[Database.Paragraph_db], list[Database.TDP_db]]:
    #     if self.dbsentences is None:
    #         raise Exception("No database sentences set")

    #     # Get distance to all other sentence embeddings
    #     distances = [ [self.cosine_similarity(query_embedding, sentence_db.embedding), sentence_db ] for sentence_db in self.dbsentences ]
    #     # Sort by distance
    #     distances.sort(key=lambda _: _[0], reverse=True)
    #     distances = distances[:20]
    #     # Add distance to sentences
    #     results = [{ 'sentence':sentence_db, 'distance': float(distance) } for distance, sentence_db in distances ]

    #     # Retrieve all paragraph ids from all selected sentences
    #     paragraph_ids = [ _['sentence'].paragraph_id for _ in results ]
    #     # Count occurences of paragraph_id
    #     paragraph_occurences = {}
    #     for paragraph_id in paragraph_ids:
    #         paragraph_occurences[paragraph_id] = paragraph_occurences.get(paragraph_id, 0) + 1
    #     paragraph_occurences = [ [k, v] for k, v in paragraph_occurences.items() ]
    #     # Sort occurences
    #     paragraph_occurences.sort(key=lambda _: _[1], reverse=True)
    #     print("[Embeddings.py][gss] paragraph_occurences", paragraph_occurences)

    #     # Get all paragraphs
    #     paragraphs = [ db_instance.get_paragraph_by_id(paragraph_id) for paragraph_id, _ in paragraph_occurences ]
    #     # Get top 3 paragraphs
    #     top_paragraphs = paragraphs[:3]
        
    #     tdp_ids = list(set([ _.tdp_id for _ in paragraphs ]))
    #     tdps = [ db_instance.get_tdp_by_id(tdp_id) for tdp_id in tdp_ids ]

    #     sentences = [ _['sentence'] for _ in results ]

    #     return sentences, top_paragraphs, tdps

    # def query(self, sentence_:str):
    #     sentence = sentence_
    #     print(f"[Embeddings.py] Querying '{sentence}'")
    #     words = [ word for word in sentence.lower().split(' ') if word not in sw_nltk ]
    #     sentence = " ".join(words)
    #     print(f"[Embeddings.py] Cleaned up '{sentence}'")
    #     query_embedding = self.embed(sentence)
    #     return *self.get_similar_sentences(query_embedding), sentence_, words


instance = Embeddor()