import numpy as np
import re

import nltk
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import stopwords
STOPWORDS_ENGLISH = stopwords.words('english')
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

def split_text_into_sentences(text:str) -> list[str]:
    ### Split into spans
    ## However, don't split on numbers, because those are often part of the span

    REGEX_OFFSET = 1 # Don't split at the end of the regex match, since that includes the first capital letter of the next span
    
    # Find all the indices of the split points
    # Note: Can't use re.split() because it drops the delimiters
    split_indices = np.array([ m.end() for m in re.finditer("[!?\.] [A-Z0-9]", text) ])
    # Append start and end of text
    split_indices = [REGEX_OFFSET] + list(split_indices) + [len(text)+REGEX_OFFSET]
    # Remove duplicates and resort (can happen when " + [len(text)+REGEX_OFFSET]" adds a duplicate )
    split_indices = sorted(list(set(split_indices)))
    
    """ Debugging
    indicator = " " * len(text)
    for i in split_indices: indicator = indicator[:i-REGEX_OFFSET] + "#" + indicator[i+1-REGEX_OFFSET:]
    # split text  up into blocks of length 80
    blocks1 = [ text     [i:i+80] for i in range(0, len(text),      80) ]
    blocks2 = [ indicator[i:i+80] for i in range(0, len(indicator), 80) ]
    # print
    for a, b in zip(blocks1, blocks2): print(f"{a}\n{b}")
    """
    
    spans = []
    for a, b in zip(split_indices, split_indices[1:]):
        span = text[a-REGEX_OFFSET:b-REGEX_OFFSET].strip()
        spans.append(span)
    
    return spans

def process_text_for_keyword_search(text:str) -> str:
    text = text.lower()
    words = re.findall(r'\w+', text)                                    # Extract words
    words = [ word for word in words if 1 < len(word)]                  # Remove single characters (slighly iffy, since it also removes useful things like 'x' and 'y')
    words = [ word for word in words if word not in STOPWORDS_ENGLISH ] # Filter out stopwords
    words = [ lemmatizer.lemmatize(word) for word in words ]            # Lemmatize
    
    sentence = " ".join(words)
    return sentence

def process_raw_spans(spans:list[str]) -> list[list[str], list[str]]:
        text_raw = "\n".join(spans)
        
        # Get rid of newlines and reconstruct hyphenated words
        text_raw = text_raw.replace("-\n", "")
        # Replace multiple whitespace with single whitespace
        text_raw = re.sub(r"\s+", " ", text_raw)
        # Replace newlines with whitespace
        text_raw = text_raw.replace("\n", " ")
        
        # references = re.findall(r"\[[0-9]+\]", text_raw) TODO
        sentences_raw = split_text_into_sentences(text_raw)
        sentences_processed = [ process_text_for_keyword_search(_) for _ in sentences_raw ]
        
        return sentences_raw, sentences_processed