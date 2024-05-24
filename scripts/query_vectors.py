# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import itertools
# Third party libraries
from custom_dotenv import load_dotenv
load_dotenv()
import numpy as np
# Local libraries
from data_access.vector.pinecone_client import PineconeClient
from data_structures.TDPName import TDPName
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
    response_questions = vector_client.query_questions(dense_vector, sparse_vector, limit=15)

    print("================ MATCHES ================")
    for i_match, match in enumerate(response_paragraph_chunks['matches']):
        metadata = match['metadata']
        print(f"Match {i_match:2}    tdp: {metadata['tdp_name']}    paragraph: {metadata['paragraph_sequence_id']}    chunk: {metadata['chunk_sequence_id']}    score: {match['score']:.2f}")
        print(metadata['text'])
        print("\n")

    print("================ QUESTIONS ================")

    # pdf_question = [ (_['metadata']['tdp_name'], _['metadata']['question']) for _ in response_questions['matches'] ]
    # groupby tdp_name
    group = itertools.groupby(response_questions['matches'], lambda q: q['metadata']['tdp_name'])

    pdfs = {}
    for response in response_questions['matches']:
        tdp_name, question = response['metadata']['tdp_name'], response['metadata']['question']
        if tdp_name not in pdfs: pdfs[tdp_name] = []
        pdfs[tdp_name].append(question)

    for pdf, questions in pdfs.items():
        tdp_name = TDPName.from_string(pdf)
        print(f"\n{tdp_name.league.name_pretty:20}  {tdp_name.team_name.name_pretty:20}  {tdp_name.year}  {len(list(questions))} questions")
        for i_question, question in enumerate(questions):
            print(f"    {i_question:2}: {question}")

        # for i_question, question in enumerate(pdf[1]):
        #     print(f"Question {i_question:2}: {question[1]}")
        # print("\n")

    # for i_match, match in enumerate(response_questions['matches']):
    #     metadata = match['metadata']
    #     print(f"Match {i_match:2}    tdp: {metadata['tdp_name']}    paragraph: {metadata['paragraph_sequence_id']}    chunk: {metadata['chunk_sequence_id']}    score: {match['score']:.2f}")
    #     print(metadata['question'])
    #     print("\n")
