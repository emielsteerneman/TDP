# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import shutil
import subprocess
import time
# Third party libraries
from openai import OpenAI
# Local libraries
import startup
from MyLogger import logger
from embedding.Embeddings import instance as embeddor
from data_access.vector.vector_filter import VectorFilter

vector_client = startup.get_vector_client()
oc = OpenAI()

n_pc = vector_client.count_paragraph_chunks()
n_q = vector_client.count_questions()

print(f"n_pc: {n_pc}, n_q: {n_q}")

query = "How do I control a small size league omniwheel robot?"
filter = VectorFilter(league="soccer_small_size")

dense_vector = embeddor.embed_dense_openai(query)
sparse_vector, keywords = embeddor.embed_sparse_prefitted_bm25(query, is_query=True)
keywords = [ _ for _ in keywords.keys() if 0.1 < keywords[_] ]

logger.debug(f"Query: {query}")
logger.debug(f"Keywords: {keywords}")
logger.debug(f"Filter: {filter}")

# Get paragraphs and questions from vector database
response_paragraph_chunks = vector_client.query_paragraph_chunks(dense_vector, sparse_vector, limit=30)
# response_questions = vector_client.query_questions(dense_vector, sparse_vector, limit=60)

# print(response_paragraph_chunks)
# print(response_questions)

for p in response_paragraph_chunks['matches']:
    metadata = p['metadata']
    print("Team:", metadata['team'])
    print("Paragraph title:", metadata['paragraph_title'])
    print("Text:", metadata['text'])
    print("\n\n\n")