# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import itertools
# Third party libraries
from dotenv import load_dotenv
load_dotenv()
import numpy as np
# Local libraries
from data_access.llm.llm_client import OpenAIClient
from data_access.vector.pinecone_client import PineconeClient
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.TDPName import TDPName
from embedding.Embeddings import instance as embeddor
from text_processing.text_processing import reconstruct_paragraph_text

vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))
llm_client = OpenAIClient()

print(f"Paragraphs: {vector_client.count_paragraphs()}    Questions: {vector_client.count_questions()}")

def summarize_by_sentence(text:str, keywords:list[str]) -> str:
    
    print("Keywords:", keywords)
    print(text)

    keywords = [ _.lower() for _ in keywords ]
    sentences = text.split(".")

    sentences = [ _.strip() for _ in sentences if any([k in _ for k in keywords]) ]
    print("---")
    print(" ... ".join(sentences))

    return " ... ".join(sentences)

while True:
    print("\n\n")
    query = input("Enter query: ")
    print()
    if query == "":
        continue

    filter={
        # "team":"RoboTeam_Twente",
        # "year":2022
    }

    dense_vector = embeddor.embed_dense_openai(query)
    sparse_vector, keywords = embeddor.embed_sparse_pinecone_bm25(query, is_query=True)
    print(keywords)
    keywords = [ _ for _ in keywords.keys() if 0.1 < keywords[_] ]

    print("sparse_vector", sparse_vector)
    # continue

    response_paragraph_chunks = vector_client.query_paragraphs(dense_vector, sparse_vector, limit=5, filter=filter)
    response_questions = vector_client.query_questions(dense_vector, sparse_vector, limit=10, filter=filter)

    scores = {}

    # print("================ PARAGRAPH CHUNKS ================")
    paragraph_chunk_matches = response_paragraph_chunks['matches'] # [ id, metadata, score, values ]
    vector_ids = [match['id'] for match in paragraph_chunk_matches]
    paragraph_chunk_questions = vector_client.get_questions_metadata_by_id(vector_ids) # [ metadata ]

    paragraphs = {}
    for i_match, match in enumerate(paragraph_chunk_matches):
        metadata = match['metadata']
        paragraph_id = f"{metadata['tdp_name']}__{int(metadata['paragraph_sequence_id'])}"
        if paragraph_id not in paragraphs: paragraphs[paragraph_id] = {
            'score': 0,
            'questions': [],
            'chunks': []
        }
        paragraphs[paragraph_id]['score'] += match['score']
        paragraphs[paragraph_id]['chunks'].append(metadata)

    for i_question, metadata in enumerate(paragraph_chunk_questions):
        paragraph_id = f"{metadata['tdp_name']}__{int(metadata['paragraph_sequence_id'])}"
        paragraphs[paragraph_id]['questions'].append(metadata)

    # print("================ QUESTIONS ================")
    question_matches = response_questions['matches'] # [ id, metadata, score, values ]
    vector_ids = [match['id'] for match in question_matches]
    question_paragraph_chunks = vector_client.get_paragraph_chunks_metadata_by_id(vector_ids) # [ metadata ]

    for i_paragraph, metadata in enumerate(question_paragraph_chunks):
        # print(f"{i_paragraph:2} ({question_matches[i_paragraph]['score']:.2f}): {metadata['text']}")
        paragraph_id = f"{metadata['tdp_name']}__{int(metadata['paragraph_sequence_id'])}"
        if paragraph_id not in paragraphs: paragraphs[paragraph_id] = {
            'score': 0,
            'questions': [],
            'chunks': []
        }
        paragraphs[paragraph_id]['chunks'].append(metadata)

    for i_question, match in enumerate(question_matches):
        metadata = match['metadata']
        paragraph_id = f"{metadata['tdp_name']}__{int(metadata['paragraph_sequence_id'])}"
        paragraphs[paragraph_id]['score'] += match['score']
        paragraphs[paragraph_id]['questions'].append(metadata)


    # print("\n\n\n\n")

    # Sort paragraphs by score, high to low
    pid_paragraphs = sorted(paragraphs.items(), key=lambda x: x[1]['score'], reverse=True)

    for pid, p in pid_paragraphs:
        print()
        print(pid, '-', p['chunks'][0]['paragraph_title'])
        print(p['score'])
        for q in p['questions']:
            print("    ", q['question'])
        for c in p['chunks']:
            print("    ", int(c['chunk_sequence_id']))

    SOURCES = ""

    for pid, p in pid_paragraphs:
        first_chunk = p['chunks'][0]
        tdp_name = TDPName.from_string(first_chunk['tdp_name'])
        paragraph_title = first_chunk['paragraph_title']
        paragraph_sequence_id = int(first_chunk['paragraph_sequence_id'])
        # print(pid, tdp_name)

        paragraph = Paragraph(
            tdp_name=tdp_name,
            text_raw=paragraph_title,
            sequence_id=paragraph_sequence_id,
        )

        chunks_uniq = {}
        for c in p['chunks']: chunks_uniq[int(c['chunk_sequence_id'])] = c
        cid_chunk = sorted(chunks_uniq.items(), key=lambda x: x[0])
        
        chunks = [_[1] for _ in cid_chunk]
        
        chunks = list(map(lambda c: ParagraphChunk(
            paragraph=paragraph,
            text=c['text'],
            sequence_id=int(c['chunk_sequence_id']),
            start=int(c['start']),
            end=int(c['end']),
        ), chunks))
            
        reconstructed_text = reconstruct_paragraph_text(chunks)
        # print("\n\n\n\n=============== NEW PARAGRAPH ================")
        # print(f"SOURCE: team={tdp_name.team_name.name} year={tdp_name.year}")
        # print(f"TEXT: | {reconstructed_text} |")

        SOURCES += "\n\n\n\n=============== NEW PARAGRAPH ================\n"
        SOURCES += f"SOURCE : | team='{tdp_name.team_name.name_pretty}', year='{tdp_name.year}', league='{tdp_name.league.name_pretty}', paragraph='{paragraph_title}' |\n"
        SOURCES += f"TEXT : | {reconstructed_text} |\n"
        SOURCES += f"SUMMARY : | {summarize_by_sentence(reconstructed_text, keywords )} |\n"

    print("\n\n\n")
    print(SOURCES)
    print("\n\n\n") 

    continue

    with open("sources.txt", "w") as f:
        f.write(SOURCES)

    print("\n\n\n======== LLM RESPONSE =========\n\n\n")
    llm_response = llm_client.answer_question(question=query, source_text=SOURCES, model="gpt-4o")
    print(llm_response)