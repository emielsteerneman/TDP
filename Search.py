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
        if source == self.SOURCE_SENTENCES:
            self.items_db = db_instance.get_sentences()
        if source == self.SOURCE_PARAGRAPHS:
            self.items_db = db_instance.get_paragraphs()
        if source == self.SOURCE_IMAGES:
            self.items_db = db_instance.get_images()
            
        print(f"[Search] Loaded {len(self.items_db)} items from database")
        
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
        
        query_processed = make_query(query)
        print(f"[Search] Searching with R={R}, T={score_threshold} for '{query}'")
        print(f"[Search] '{query_processed}'")
        
        query_embedding = embed_instance.embed(query_processed)
        
        """ Get vector similarities """
        now = time.time()
        similarities = np.array([ embed_instance.cosine_similarity(query_embedding, item.embedding) for item in self.items_db ])
        print(f"[Search] Calculated {len(similarities)} similarities ({int(1000*(time.time() - now))}ms)")

        """ Get doc scores """
        tokenized_query = [ word for word in query_processed.lower().split(' ') ]
        now = time.time()
        doc_scores = self.bm25.get_scores(tokenized_query)
        print(f"[Search] Calculated {len(doc_scores)} doc scores ({int(1000*(time.time() - now))}ms)")
        
        """ Process results """
        similarities_normalized = similarities #= (similarities - np.min(similarities)) / (np.max(similarities) + 0.00001 - np.min(similarities))
        doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) + 0.00001 - np.min(doc_scores))

        """ Print top 3 results of both"""
        print("\n[Search] Top 3 context results")
        argsort = np.argsort(similarities)[::-1][:3]
        for i in argsort:
            print(f"{i} - {similarities[i]:.2f} - {similarities_normalized[i]:.2f} vs {doc_scores_normalized[i]:.2f} | {self.items_db[i].text_raw}")
        
        print("\n[Search] Top 3 keyword results")
        argsort = np.argsort(doc_scores)[::-1][:3]
        for i in argsort:
            print(f"{i} - {doc_scores[i]:.2f} - {doc_scores_normalized[i]:.2f} vs {similarities_normalized[i]:.2f} | {self.items_db[i].text_raw}")
        print()

        """ Calculate item scores """
        item_scores = R * np.array( similarities_normalized ) + (1-R) * np.array( doc_scores_normalized )
        
        """ Return top n items """
        argsort = np.argsort(item_scores)[::-1][:n]                          # Sort scores
        argsort = [ _ for _ in argsort if item_scores[_] > score_threshold ] # Filter by score threshold
        items = [ self.items_db[i] for i in argsort ]                        # Get items
        
        print(f"[Search] Completed search in {int(1000*(time.time() - time_search_start))}ms")
        if(len(argsort)):
            print(f"[Search] Most relevant item: '{self.items_db[argsort[0]].text_raw}'\n")
        else:
            print(f"[Search] No relevant items found\n")
            
        
        return items, item_scores[argsort]
    
    def sentences_to_paragraphs(self, sentences_db:list, item_scores:np.array=None, n=3):
        # paragraph_ids = list(set([ _['paragraph_id'] for _ in sentences_db ]))
        
        if item_scores is None:
            item_scores = np.ones(len(sentences_db))
        
        paragraph_scores = {}
        paragraph_count = {}
        for sentence, score in list(zip(sentences_db, item_scores)):
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

def load_paragraphs(query_):
    # Query to group sentences by paragraph
    query = """
        SELECT sentences.paragraph_id, GROUP_CONCAT(sentences.text, ' . ') AS text, GROUP_CONCAT(sentences.text_raw, ' . ') AS text_raw, paragraphs.title FROM sentences
        INNER JOIN paragraphs ON sentences.paragraph_id = paragraphs.id
        GROUP BY sentences.paragraph_id
        """
    ts = time.time()
    results = db_instance.execute_query(query)
    print(f"[Search] Loaded {len(results)} paragraphs in {int(1000*(time.time() - ts))}ms")
    
    for paragraph in results[:3]:
        print(paragraph['title'])
        print(paragraph['text'])
        print()
        
    now = time.time()
    tokenized_corpus = [ _['text'].split(" ") for _ in results ]
    bm25 = BM25Okapi(tokenized_corpus)
    print(f"[Search][reload_corpus] Created BM25 model of size {bm25.corpus_size} ({int(1000*(time.time() - now))}ms)")
    
        
        
    time_search_start = time.time()
        
    query = make_query(query_)
    print(f"[Search] Searching for '{query_}'")
    print(f"[Search] '{query}'")
    
    """ Get doc scores """
    tokenized_query = [ word for word in query.lower().split(' ') if word not in sw_nltk ]
    now = time.time()
    doc_scores = bm25.get_scores(tokenized_query)
    print(f"[Search] Calculated {len(doc_scores)} doc scores ({int(1000*(time.time() - now))}ms)")
    
    """ Process results """
    doc_scores_normalized = (doc_scores - np.min(doc_scores)) / (np.max(doc_scores) + 0.00001 - np.min(doc_scores))

    print("\n[Search] Top 3 keyword results")
    argsort = np.argsort(doc_scores)[::-1][:3]
    for i in argsort:
        print(f"{i} - {doc_scores[i]:.2f} - {doc_scores_normalized[i]:.2f}")
    print()

    """ Calculate sentence scores """
    item_scores = np.array( doc_scores_normalized )
    
    """ Return top n sentences """
    argsort = np.argsort(item_scores)[::-1]                          # Sort scores
    argsort = [ _ for _ in argsort if item_scores[_] > 0.1 ]         # Filter by score threshold
    paragraphs = [ results[i] for i in argsort ]                         # Get sentences
    
    print(f"[Search] Completed search in {int(1000*(time.time() - time_search_start))}ms")
    if(len(argsort)):
        print(f"[Search] Most relevant sentence: '{results[argsort[0]]['text']}'\n")
        print(f"[Search] Most relevant sentence: '{results[argsort[0]]['text_raw']}'\n")
    else:
        print(f"[Search] No relevant sentences found\n")
        
        
    print("\n\n\n")

    keywords = query.split(" ") 
    print(keywords)       
    
    for p in results:
        if all([ _.lower() in p['text'].lower() for _ in keywords ]):
            print(p['text_raw'])
            print()
    
# instance = Search()

if __name__ == "__main__":
    print("[Search] Running search.py as main")
    
    # load_paragraphs("dribbler reinforcement learning")
    # exit()
    
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
    
    # query = "I want to know more about material for the dribbler"
    # query = "What is a better dribbler material ? Silicon or rubber ?"
    # sentences, scores = instance.search(query, R=0)
    # instance.sentences_to_paragraphs(sentences, scores)
    
    # sentences, scores = instance.search(query, R=0.5)
    # instance.sentences_to_paragraphs(sentences, scores)
    
    # sentences, scores = instance.search(query, R=1)
    # instance.sentences_to_paragraphs(sentences, scores)