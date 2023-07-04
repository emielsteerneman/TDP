import Database
from Database import instance as db_instance

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

sentences = db_instance.get_sentences_exhaustive()[:10]

paragraphs = db_instance.get_paragraphs()

print(paragraphs[0].text)

texts = [ paragraph.text for paragraph in paragraphs ]

# exit()
# word_count = {}

# for sentence in sentences:
#     sentence['embedding'] = None
#     print(sentence)
#     words = sentence['text'].split(' ')
#     for word in words:
#         if word not in word_count:
#             word_count[word] = 0
#         word_count[word] += 1
        
# # print(word_count)

# # Sort words on occurence and print
# word_count = [ [k, v] for k, v in word_count.items() ]
# word_count.sort(key=lambda _: _[1], reverse=True)
# for word, count in word_count:
#     print(f"{word} : {count}")
    
    
    
    
documents = [ sentence['text'] for sentence in sentences ]

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(texts)
feature_names = vectorizer.get_feature_names_out()
dense = vectors.todense()
denselist = dense.tolist()

# 2d matrix
denselist_np = np.array(denselist)

# Apply np.argpartition to 2d matrix, to get top 5 results in each row
# https://stackoverflow.com/questions/6910641/how-do-i-get-indices-of-n-maximum-values-in-a-numpy-array
argpart = np.argpartition(denselist_np, -3)[:, -3:]

scores = denselist_np[np.arange(denselist_np.shape[0])[:,None], argpart]

print(np.max(denselist, axis=1))

for x in denselist_np:
    max_, argmax = np.max(x), np.argmax(x)
    print(f"{max_:.3f} at {argmax}: {feature_names[argmax]}")

for row in argpart:
    print([ feature_names[i] for i in row ])

# df = pd.DataFrame(denselist, columns=feature_names)
  
    
    