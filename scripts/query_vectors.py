# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Third party libraries
from custom_dotenv import load_dotenv
load_dotenv()
import numpy as np
# Local libraries
from data_access.vector.pinecone_client import PineconeClient
from embedding.Embeddings import instance as embeddor


vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))

while True:
    print("\n\n")
    query = input("Enter query: ")
    if query == "":
        continue

    dense_vector = embeddor.embed_using_openai(query)
    sparse_vector = embeddor.sparse_embed_using_bm25(query, is_query=True)

    response_paragraph_chunks = vector_client.query_paragraphs(dense_vector, sparse_vector, limit=3)
    response_questions = vector_client.query_questions(dense_vector, sparse_vector, limit=3)

    print("================ MATCHES ================")
    for i_match, match in enumerate(response_paragraph_chunks['matches']):
        metadata = match['metadata']
        print(f"Match {i_match:2}    tdp: {metadata['tdp_name']}    paragraph: {metadata['paragraph_sequence_id']}    chunk: {metadata['chunk_sequence_id']}    score: {match['score']:.2f}")
        print(metadata['text'])
        print("\n")

    print("================ QUESTIONS ================")
    for i_match, match in enumerate(response_questions['matches']):
        metadata = match['metadata']
        print(f"Match {i_match:2}    tdp: {metadata['tdp_name']}    paragraph: {metadata['paragraph_sequence_id']}    chunk: {metadata['chunk_sequence_id']}    score: {match['score']:.2f}")
        print(metadata['question'])
        print("\n")