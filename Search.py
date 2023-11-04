print("[Search] Initializing search.py")

import time 
import re
import numpy as np

import Database
from Database import instance as db_instance
from Embeddings import instance as embed_instance
from rank_bm25 import BM25Okapi

import nltk
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
STOPWORDS_ENGLISH = stopwords.words('english')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()


def process_text_for_keyword_search(text:str) -> str:
    text = text.lower()
    words = re.findall(r'\w+', text)                                    # Extract words
    words = [ word for word in words if 1 < len(word)]                  # Remove single characters (slighly iffy, since it also removes useful things like 'x' and 'y')
    words = [ word for word in words if word not in STOPWORDS_ENGLISH ] # Filter out stopwords
    words = [ lemmatizer.lemmatize(word) for word in words ]            # Lemmatize
    
    sentence = " ".join(words)
    return sentence

def make_query(query_:str):
    return process_text_for_keyword_search(query_)
    
class Search:
    SOURCE_SENTENCES = "sentences"
    SOURCE_PARAGRAPHS = "paragraphs"
    SOURCE_IMAGES = "images"
    
    def __init__(self, source) -> None:
        # Load all sentences. Memory usage should be fine(ish)

        now = time.time()
        if source == self.SOURCE_SENTENCES:
            self.items_db = db_instance.get_sentences()
        if source == self.SOURCE_PARAGRAPHS:
            self.items_db = db_instance.get_paragraphs()
        if source == self.SOURCE_IMAGES:
            self.items_db = db_instance.get_images()
        self.source = source
        print(f"[Search] Loaded {len(self.items_db)} {source} from database ({int(1000*(time.time() - now))}ms)")
        self.reload_corpus()

    def reload_corpus(self):
        now = time.time()
        tokenized_corpus = [_.text_processed.split(" ") for _ in self.items_db]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"[Search][reload_corpus] Created BM25 model of size {self.bm25.corpus_size} ({int(1000*(time.time() - now))}ms)")
        
    def search(self, query:str, R:float=0.5, n:int=2000, score_threshold:float=0.1):
        """ Given a query, sort all items by relevance

        Args:
            query_ (str): Query string. Example: "I want to know more about material for the dribbler"
            R (float, optional): Weight, between 0 and 1, given to keyword similarity and context similarity. 0=keyword, 1=context. Defaults to 0.5.
            n (int, optional): _description_. Defaults to 20.
        """        
        
        time_search_start = time.time()
        time_passed = lambda: int(1000*(time.time() - time_search_start))
        time_passed_str = lambda: ("      " + str(time_passed()))[-4:] + " ms"
        log = lambda *args, **kwargs: print(f"[Search][{self.source}][{time_passed_str()}]", *args, **kwargs)

        log(f"Searching with R={R}, T={score_threshold} for '{query}'")
        query_processed = make_query(query)
        log(f"Processed query: '{query_processed}'")
        
        query_embedding = embed_instance.embed(query_processed)
        
        """ Get vector similarities """
        similarities = np.array([ embed_instance.cosine_similarity(query_embedding, item.embedding) for item in self.items_db ])
        log(f"Calculated {len(similarities)} vector similarities")

        """ Get doc scores """
        tokenized_query = [ word for word in query_processed.lower().split(' ') ]
        doc_scores = self.bm25.get_scores(tokenized_query)
        log(f"Calculated {len(doc_scores)} doc scores")
        
        """ Process results """
        similarities_normalized = similarities #= (similarities - np.min(similarities)) / (np.max(similarities) + 0.00001 - np.min(similarities))
        doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) + 0.00001 - np.min(doc_scores))

        """ Print top 3 results of both"""
        # log(f"Top 3 context results")
        # argsort = np.argsort(similarities)[::-1][:3]
        # for i in argsort:
        #     print(f"{str(i).rjust(5)} - {similarities[i]:.2f} - {similarities_normalized[i]:.2f} vs {doc_scores_normalized[i]:.2f} | {self.items_db[i].text_raw}")
        
        # if(self.source == self.SOURCE_SENTENCES):
        #     log(f"Top 3 keyword results")
        #     argsort = np.argsort(doc_scores)[::-1][:3]
        #     for i in argsort:
        #         print(f"{i} - {doc_scores[i]:.2f} - {doc_scores_normalized[i]:.2f} vs {similarities_normalized[i]:.2f} | {self.items_db[i].text_raw}")
        #     print()
        
        """ Calculate item scores """
        item_scores = R * np.array( similarities_normalized ) + (1-R) * np.array( doc_scores_normalized )
        
        """ Return top n items """
        argsort = np.argsort(item_scores)[::-1][:n]                          # Sort scores
        argsort = [ _ for _ in argsort if item_scores[_] > score_threshold ] # Filter by score threshold
        items = [ self.items_db[i] for i in argsort ]                        # Get items
        
        log(f"Completed search")
        # if(len(argsort)):
        #     log(f"Most relevant item: '{self.items_db[argsort[0]].text_raw}'\n")
        # else:
        #     log(f"No relevant items found\n")
            
        return items, item_scores[argsort]

if __name__ == "__main__":
    print("[Search] Running search.py as main")
    
    search_instance_sentences = Search(Search.SOURCE_SENTENCES)
    search_instance_paragraphs = Search(Search.SOURCE_PARAGRAPHS)
    search_instance_images = Search(Search.SOURCE_IMAGES)

    
    query = "dribbler shape conical"
    
    print("Sentence search")
    sentences, _ = search_instance_sentences.search(query, R=0.5, n=3)
    for s in sentences:
        print("*", s.text_raw)

    print("\nParagraph search")
    paragraphs, _ = search_instance_paragraphs.search(query, R=0.5, n=3)
    for p in paragraphs:
        print("*", p.title)

    print("\nImage search")
    images, _ = search_instance_images.search(query, R=0.5, n=3)
    for i in images:
        print("*", i.text_raw)