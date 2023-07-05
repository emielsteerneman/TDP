print("[Search] Initializing search.py")

import nltk
# nltk.download('stopwords')
from nltk.corpus import stopwords
sw_nltk = stopwords.words('english')

import Database
from Database import instance as db_instance
from Embeddings import Embeddor as E
import time 
from rank_bm25 import BM25Okapi
import numpy as np

def query_to_words(text:str):
    return [ word for word in text.lower().split(' ') if word not in sw_nltk ]

def filter_stopwords(text:str):
    return " ".join(query_to_words(text))

def make_query(query_:str):
    query = query_
    # print(query)
    # print(filter_stopwords(query))
    return filter_stopwords(query)
    
class Search:
    def __init__(self) -> None:
        # Load all sentences. Memory usage should be fine(ish)
        self.sentences_db = db_instance.get_sentences()
        print(f"[Search] Loaded {len(self.sentences_db)} sentences from database")
        
        self.reload_corpus()

    def reload_corpus(self):
        now = time.time()
        tokenized_corpus = [_.text.split(" ") for _ in self.sentences_db]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"[Search][reload_corpus] Created BM25 model of size {self.bm25.corpus_size} ({int(1000*(time.time() - now))}ms)")
        
    def search(self, query_:str, R:float=0.5, n:int=2000):
        """ Given a query, sort all sentences by relevance

        Args:
            query_ (str): Query string. Example: "I want to know more about material for the dribbler"
            R (float, optional): Weight, between 0 and 1, given to keyword similarity and context similarity. 0=keyword, 1=context. Defaults to 0.5.
            n (int, optional): _description_. Defaults to 20.
        """        
        time_search_start = time.time()
        
        query = make_query(query_)
        print(f"[Search] Searching with R={R} for '{query_}'")
        print(f"[Search] '{query}'")
        
        query_embedding = E.embed(query)
        
        """ Get vector similarities """
        now = time.time()
        similarities = np.array([ E.cosine_similarity(query_embedding, sentence.embedding) for sentence in self.sentences_db ])
        print(f"[Search] Calculated {len(similarities)} similarities ({int(1000*(time.time() - now))}ms)")

        """ Get doc scores """
        tokenized_query = [ word for word in query.lower().split(' ') if word not in sw_nltk ]
        now = time.time()
        doc_scores = self.bm25.get_scores(tokenized_query)
        print(f"[Search] Calculated {len(doc_scores)} doc scores ({int(1000*(time.time() - now))}ms)")
       
        """ Process results """
        similarities_normalized = (similarities - np.min(similarities)) / (np.max(similarities) - np.min(similarities))
        doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) - np.min(doc_scores))

        """ Print top 3 results of both"""
        print("\n[Search] Top 3 context results")
        argsort = np.argsort(similarities)[::-1][:3]
        for i in argsort:
            print(f"{i} - {similarities[i]:.2f} - {similarities_normalized[i]:.2f} vs {doc_scores_normalized[i]:.2f} | {self.sentences_db[i].text_raw}")
        
        print("\n[Search] Top 3 keyword results")
        argsort = np.argsort(doc_scores)[::-1][:3]
        for i in argsort:
            print(f"{i} - {doc_scores[i]:.2f} - {doc_scores_normalized[i]:.2f} vs {similarities_normalized[i]:.2f} | {self.sentences_db[i].text_raw}")
        print()

        """ Calculate sentence scores """
        sentence_scores = R * np.array( similarities_normalized ) + (1-R) * np.array( doc_scores_normalized )
        
        """ Return top n sentences """
        argsort = np.argsort(sentence_scores)[::-1][:n]
        sentences = [ self.sentences_db[i] for i in argsort ]
        
        print(f"[Search] Completed search in {int(1000*(time.time() - time_search_start))}ms")
        print(f"[Search] Most relevant sentence: '{self.sentences_db[argsort[0]].text_raw}'\n")
        
        return sentences, sentence_scores[argsort]
    
    def sentences_to_paragraphs(self, sentences_db:list, sentence_scores:np.array=None, n=3):
        # paragraph_ids = list(set([ _['paragraph_id'] for _ in sentences_db ]))
        
        if sentence_scores is None:
            sentence_scores = np.ones(len(sentences_db))
        
        paragraph_scores = {}
        paragraph_count = {}
        for sentence, score in list(zip(sentences_db, sentence_scores)):
            pid = sentence.paragraph_id
            if pid not in paragraph_scores: paragraph_scores[pid] = 0
            paragraph_scores[pid] += score
            if pid not in paragraph_count: paragraph_count[pid] = 0
            paragraph_count[pid] += 1
            
        paragraph_scores = [ [k, v / min(paragraph_count[k], 5) ] for k, v in paragraph_scores.items() ]
        paragraph_scores.sort(key=lambda _: _[1], reverse=True)
        for paragraph_id, score in paragraph_scores[:n]:
            paragraph_db = db_instance.get_paragraph_by_id(paragraph_id)
            tdp_db = db_instance.get_tdp_by_id(paragraph_db.tdp_id)
            print("    ", score, tdp_db.year, tdp_db.team, paragraph_db.title)
        
        paragraph_ids = [ _[0] for _ in paragraph_scores ][:n]
        
        return paragraph_ids

instance = Search()

if __name__ == "__main__":
    print("[Search] Running search.py as main")
    
    # query = "I want to know more about material for the dribbler"
    query = "What is a better dribbler material ? Silicone or rubber ?"
    sentences, scores = instance.search(query, R=0)
    instance.sentences_to_paragraphs(sentences, scores)
    
    sentences, scores = instance.search(query, R=0.5)
    instance.sentences_to_paragraphs(sentences, scores)
    
    sentences, scores = instance.search(query, R=1)
    instance.sentences_to_paragraphs(sentences, scores)