print("[Search] Initializing search.py")

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
sw_nltk = stopwords.words('english')

def filter_stopwords(text):
    return " ".join([ word for word in text.lower().split(' ') if word not in sw_nltk ])

def make_query(query_):
    query = query_.lower()
    print(query)
    print(filter_stopwords(query))
    
    

if __name__ == "__main__":
    print("[Search] Running search.py as main")
    
    # query = input("Query: ")
    query = "I want to know more about material for the dribbler"
    make_query(query)