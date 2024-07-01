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
from data_structures.Sentence import Sentence
from data_structures.TDPName import TDPName
from embedding.Embeddings import instance as embeddor
from text_processing.text_processing import reconstruct_paragraph_text

vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))
llm_client = OpenAIClient()

def summarize_by_sentence(text:str, keywords:list[str]) -> str:
    keywords = [ _.lower() for _ in keywords ]
    sentences = text.split(".")
    sentences = [ _.strip() for _ in sentences if any([k in _ for k in keywords]) ]
    summary = " ... ".join(sentences)

    if not len(summary):
        return text
    
    return summary

def summarize(text:str, keywords:list[str], T=20, N=3) -> str:

    keywords = [ _.lower() for _ in keywords ]
    words = text.split(" ")

    indices = [ i for i, word in enumerate(words) if any([ word.lower().startswith(k) for k in keywords ]) ]
    differences = np.diff(indices)

    ranges = []

    i = 0
    if len(differences):

        indices_distance = list(zip(indices[1::], differences, differences[1::]))
        indices_distance = [ (indices[0], 999, differences[0]) ] + indices_distance + [ (indices[-1], differences[-1], 999) ]
        # print(indices_distance)
        # print()

        indices_distance = [ (a,b,c) for (a,b,c) in indices_distance if T<b or T<c ]
        # print(indices_distance)

        while True:
            # print(f"{i} / {len(indices_distance)}")
            if len(indices_distance) <= i: break
            at = indices_distance[i]

            if i < len(indices_distance)-1:
                atnext = indices_distance[i+1]

            if T < at[1] and T < at[2]:
                # print("\nFOUND SINGLE")
                # print(at)
                ranges.append([ max(0, at[0]-N), min(len(words), at[0]+N) ])
                i += 1
            elif T < at[1] and T < indices_distance[i+1][2]:
                # print("\nFOUND DOUBLE")
                # print(at, indices_distance[i+1])
                ranges.append([ max(0, at[0]-N), min(len(words), atnext[0]+N) ])
                i += 2
            else:
                raise Exception("wtf")
    else:
        at = indices[0]
        ranges.append([ at-3*N, at+3*N ])

    # ranges = [ ( max(0, r[0]), min(len(words), r[0]) ) for r in ranges ]

    sentences = []
    for a, b in ranges:
        # print()
        # print(f"  {a:4} {b:4}")
        sentence = " ".join(words[a:b])
        sentences.append(sentence)

    return " ... ".join(sentences)



def search(vector_client:PineconeClient, query:str, filter={}, compress_text=False) -> list[Paragraph]:
    if query == "": return []

    filter={
        # "team":"RoboTeam_Twente",
        # "year":2022
    }

    dense_vector = embeddor.embed_dense_openai(query)
    sparse_vector, keywords = embeddor.embed_sparse_pinecone_bm25(query, is_query=True)
    print(keywords)
    keywords = [ _ for _ in keywords.keys() if 0.1 < keywords[_] ]

    # Get paragraphs and questions from vector database
    response_paragraph_chunks = vector_client.query_paragraphs(dense_vector, sparse_vector, limit=15, filter=filter)
    response_questions = vector_client.query_questions(dense_vector, sparse_vector, limit=30, filter=filter)


    """ Paragraph metadata:
    
    tdp_name: "soccer_smallsize__2016__Parsian__0"
    paragraph_sequence_id: 13
    chunk_sequence_id: 0
    league: "soccer_smallsize"
    year: 2016
    team: "Parsian"
    paragraph_title: "5.1. Architecture"
    run_id: "7fc22e94-b9ae-4f57-a647-1f4096696e43"
    
    start: 0
    end: 181
    text: "This year the software architecture has some minor changes that will be discussed in the next part. Here is The Parisan Software architecture chart (Fig.10). Fig.10. Software chart "

    """

    """ Question metadata:
    tdp_name: "soccer_smallsize__2013__Stanford_Robotics_Club__0"
    paragraph_sequence_id: 6
    chunk_sequence_id: 2
    league: "soccer_smallsize"
    year: 2013
    team: "Stanford_Robotics_Club"
    paragraph_title: "2.5 Kicker"
    
    question: "What are some factors to consider when choosing between an ironless or slotless steel forcer?"
    """

    paragraphs = {}

    # print("================ PARAGRAPH CHUNKS ================")
    # Get paragraph chunks
    paragraph_chunk_matches = response_paragraph_chunks['matches'] # [ id, metadata, score, values ]
    # Get the questions that are associated with the paragraph chunks
    vector_ids = [match['id'] for match in paragraph_chunk_matches]
    paragraph_chunk_questions = vector_client.get_questions_metadata_by_id(vector_ids) # [ metadata ]
    
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
    # Get questions
    question_matches = response_questions['matches'] # [ id, metadata, score, values ]
    # Get the paragraph chunks that are associated with the questions
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


    # print("================ POST PROCESS ================")

    # Sort paragraphs by score, high to low
    pid_paragraphs = sorted(paragraphs.items(), key=lambda x: x[1]['score'], reverse=True)

    # for pid, p in pid_paragraphs:
    #     print()
    #     print(pid, '-', p['chunks'][0]['paragraph_title'])
    #     print(p['score'])
    #     for q in p['questions']:
    #         print("    ", q['question'])
    #     for c in p['chunks']:
    #         print("    ", int(c['chunk_sequence_id']))

    SOURCES = ""

    reconstructed_paragraphs: list[Paragraph] = []

    # pid_paragraph: { score, questions:[], chunks:[] }

    for pid, p in pid_paragraphs:

        first_chunk = p['chunks'][0]
        tdp_name = TDPName.from_string(first_chunk['tdp_name'])
        paragraph_title = first_chunk['paragraph_title']
        paragraph_sequence_id = int(first_chunk['paragraph_sequence_id'])

        paragraph = Paragraph(
            tdp_name=tdp_name,
            text_raw=paragraph_title,
            sequence_id=paragraph_sequence_id
        )
        
        chunks_uniq = {} # { chunk_sequence_id: chunk }
        for chunk in p['chunks']: chunks_uniq[int(chunk['chunk_sequence_id'])] = chunk
        csid_chunk = sorted(chunks_uniq.items(), key=lambda x: x[0])
        chunks = [_[1] for _ in csid_chunk]
     
        chunks = list(map(lambda c: ParagraphChunk(
            paragraph=paragraph,
            text=c['text'],
            sequence_id=int(c['chunk_sequence_id']),
            start=int(c['start']),
            end=int(c['end']),
        ), chunks))
            
        reconstructed_text = reconstruct_paragraph_text(chunks)

        if compress_text:
            reconstructed_text = summarize_by_sentence(reconstructed_text, keywords)

        # TODO fix ugly hack
        paragraph.sentences.append(Sentence(text_raw=reconstructed_text))

        questions = list(set([ q_metadata['question'] for q_metadata in p['questions'] ] ))
        paragraph.questions = questions

        reconstructed_paragraphs.append(paragraph)

        # print("\n\n\n\n=============== NEW PARAGRAPH ================")
        # print(f"SOURCE: team={tdp_name.team_name.name} year={tdp_name.year}")
        # print(f"TEXT: | {reconstructed_text} |")

        # SOURCES += "\n\n\n\n=============== NEW PARAGRAPH ================\n"
        # SOURCES += f"SOURCE : | team='{tdp_name.team_name.name_pretty}', year='{tdp_name.year}', league='{tdp_name.league.name_pretty}', paragraph='{paragraph_title}' |\n"
        # SOURCES += f"TEXT : | {reconstructed_text} |"
    
    return reconstructed_paragraphs, keywords

    print("\n\n\n")
    print(SOURCES)
    print("\n\n\n") 

    print("\n\n\n======== LLM RESPONSE =========\n\n\n")
    llm_response = llm_client.answer_question(question=query, source_text=SOURCES, model="gpt-4o")
    print(llm_response)