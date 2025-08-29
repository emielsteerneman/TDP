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


def reconstruct_paragraphs(paragraphs):
    """
    paragraphs = {
        "tdp_name__paragraph_sequence_id": {
            'score': float,
            'questions': [ { question, ... } ],
            'chunks': [ { text, ... } ]
        }
    }
    """
    pass


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

# for p in response_paragraph_chunks['matches']:
#     metadata = p['metadata']
#     print("Team:", metadata['team'])
#     print("Paragraph title:", metadata['paragraph_title'])
#     print("Text:", metadata['text'])
#     print("\n\n\n")
#     continue


# ================ PARAGRAPH CHUNKS ================
# Get paragraph chunks
paragraph_chunk_matches = response_paragraph_chunks['matches'] # [ id, metadata, score, values ]
# Get the questions that are associated with the paragraph chunks
chunk_ids = [match['id'] for match in paragraph_chunk_matches]

print(chunk_ids)

if not len(chunk_ids):
    logger.debug("No matches found. Returning empty results")        
    exit()


paragraphs = {}
# For all paragraph chunks, prepare or add to the paragraph
for i_match, match in enumerate(paragraph_chunk_matches):
    metadata = match['metadata']
    paragraph_id = f"{metadata['tdp_name']}__{int(metadata['paragraph_sequence_id'])}"
    if paragraph_id not in paragraphs: paragraphs[paragraph_id] = {
        'score': 0,
        'chunks': []
    }
    paragraphs[paragraph_id]['score'] += match['score']
    paragraphs[paragraph_id]['chunks'].append(metadata)

# ================ POST PROCESS ================

"""
paragraphs = {
    "tdp_name__paragraph_sequence_id": {
        'score': float,
        'chunks': [ { text, ... } ]
    }
}
"""

# Sort paragraphs by score, high to low
paragraphs_sorted = sorted(paragraphs.values(), key=lambda _: _['score'], reverse=True)

# SOURCES = ""
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.TDPName import TDPName

reconstructed_paragraphs: list[Paragraph] = []

scores = [ f"{p['score']:.2f}" for p in paragraphs_sorted ]

for ip, p in enumerate(paragraphs_sorted):

    if p['score'] < 0.5: continue

    first_chunk = p['chunks'][0]
    tdp_name = TDPName.from_string(first_chunk['tdp_name'])
    paragraph_title = first_chunk['paragraph_title']
    paragraph_sequence_id = int(first_chunk['paragraph_sequence_id'])

    # Create paragraph object
    paragraph = Paragraph(
        tdp_name=tdp_name,
        text_raw=paragraph_title,
        sequence_id=paragraph_sequence_id
    )
    
    # Get a unique list of chunks and sort by chunk_sequence_id
    chunks_uniq = {} # { chunk_sequence_id: chunk }
    for chunk in p['chunks']: chunks_uniq[int(chunk['chunk_sequence_id'])] = chunk
    csid_chunk = sorted(chunks_uniq.items(), key=lambda x: x[0]) # [ (chunk_sequence_id, chunk) ]
    chunks = [_[1] for _ in csid_chunk]

    # Convert to ParagraphChunk objects
    chunks = list(map(lambda c: ParagraphChunk(
        paragraph=paragraph,
        text=c['text'],
        sequence_id=int(c['chunk_sequence_id']),
        start=int(c['start']),
        end=int(c['end']),
    ), chunks))
    
    # Reconstruct the paragraph text
    reconstructed_text = reconstruct_paragraph_text(chunks)

    # Compress the text
    if compress_text:
        reconstructed_text = summarize_by_sentence(reconstructed_text, keywords)

    # TODO fix ugly hack. Paragraph with single sentence, with that single sentence being all the reconstructed text
    paragraph.sentences.append(Sentence(text_raw=reconstructed_text))

    # Get a unique list of questions and add to paragraph
    questions = list(set([ q_metadata['question'] for q_metadata in p['questions'] ] ))
    paragraph.questions = questions

    reconstructed_paragraphs.append(paragraph)

    # Do some logging that might be interesting
    if ip < 5:
        logger.info(f"result: tdpname={paragraph.tdp_name} score={p['score']:.2f}")
        logger.info(f"result: questions={questions}")
        logger.info(f"result: text={reconstructed_text}")
        logger.info("")

    # SOURCES += "\n\n\n\n=============== NEW PARAGRAPH ================\n"
    # SOURCES += f"SOURCE : | team='{tdp_name.team_name.name_pretty}', year='{tdp_name.year}', league='{tdp_name.league.name_pretty}', paragraph='{paragraph_title}' |\n"
    # SOURCES += f"TEXT : | {reconstructed_text} |"
