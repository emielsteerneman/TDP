print("[Search] Initializing search.py")

import nltk
# nltk.download('stopwords')
from nltk.corpus import stopwords
sw_nltk = stopwords.words('english')

import Database
from Database import instance as db_instance
from embeddings import Embeddor as E
import time 
from rank_bm25 import BM25Okapi
import numpy as np

def filter_stopwords(text:str):
    return " ".join([ word for word in text.lower().split(' ') if word not in sw_nltk ])

def make_query(query_:str):
    query = query_
    # print(query)
    # print(filter_stopwords(query))
    return filter_stopwords(query)
    
class Search:
    def __init__(self) -> None:
        # Load all sentences. Memory usage should be fine(ish)
        self.sentences_dict = db_instance.get_sentences_exhaustive()
        print(f"[Search] Loaded {len(self.sentences_dict)} sentences from database")
        
        self.reload_corpus()

    def reload_corpus(self):
        now = time.time()
        tokenized_corpus = [_['text'].split(" ") for _ in self.sentences_dict]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"[Search][reload_corpus] Created BM25 model of size {self.bm25.corpus_size} ({int(1000*(time.time() - now))}ms)")
        
    def search(self, query_:str, R:float=0.5, n:int=20):
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
        similarities = np.array([ E.cosine_similarity(query_embedding, sentence['embedding']) for sentence in self.sentences_dict ])
        print(f"[Search] Calculated {len(similarities)} similarities ({int(1000*(time.time() - now))}ms)")

        """ Get doc scores """
        tokenized_query = [ word for word in query.lower().split(' ') if word not in sw_nltk ]
        now = time.time()
        doc_scores = self.bm25.get_scores(tokenized_query)
        print(f"[Search] Calculated {len(doc_scores)} doc scores ({int(1000*(time.time() - now))}ms)")

        """ Process results """
        similarities_normalized = (similarities - np.min(similarities)) / (np.max(similarities) - np.min(similarities))
        doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) - np.min(doc_scores))

        """ Calculate sentence scores """
        sentence_scores = R * np.array( similarities_normalized ) + (1-R) * np.array( doc_scores_normalized )
        
        """ Return top n sentences """
        argsort = np.argsort(sentence_scores)[::-1]
        sentences = [ self.sentences_dict[i] for i in argsort ]
        
        print(f"[Search] Completed search in {int(1000*(time.time() - time_search_start))}ms")
        print(f"[Search] Most relevant sentence: '{self.sentences_dict[argsort[0]]['text_raw']}'\n")
        
        return sentences
        
instance = Search()

if __name__ == "__main__":
    print("[Search] Running search.py as main")
    
    query = "I want to know more about material for the dribbler"
    instance.search(query, R=0)
    instance.search(query, R=0.5)
    instance.search(query, R=1)