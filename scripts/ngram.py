# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import time
# Third party libraries
import matplotlib.pyplot as plt
import numpy as np
# Local libraries
import startup
from data_access.file.file_client import LocalFileClient
from data_access.vector.pinecone_client import PineconeClient
from data_structures.TDPName import TDPName
from data_structures.TDPStructure import TDPStructure
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from extraction import extractor
from embedding.Embeddings import instance as embeddor

file_client:LocalFileClient = startup.get_file_client()
vector_client:PineconeClient = startup.get_vector_client()


def get_paragraphs(name:str) -> str:
    tdp_path = file_client.get_pdf(TDPName.from_string(name), no_copy=True)
    tdp_structure:TDPStructure = extractor.process_pdf(tdp_path)
    return tdp_structure.paragraphs

def create_paragraph_chunks(paragraph:Paragraph, n_chars_per_group:int = 2000, n_chars_overlap:int = 500) -> list[ParagraphChunk]:
    """ Function to split a paragraph into chunks of approximately n_chars_per_group characters, with an overlap of n_chars_overlap characters between
    each chunk. The function will ensure that no two chunks start at the same sentence, thus avoiding duplicate chunks.

    Args:
        paragraph (Paragraph): The paragraph to split into chunks
        n_chars_per_group (int, optional): The desired number of characters of each chunk. Will be equal to or less than this number. Defaults to 2000.
        n_chars_overlap (int, optional): The number of characters that each chunk should overlap with the previous chunk. Defaults to 500.

    Returns:
        list[ParagraphChunk]: A list of ParagraphChunk objects, each representing a chunk of the paragraph
    """

    chunks:list[ParagraphChunk] = []
    sentences:list[str] = [ _.text_raw for _ in paragraph.sentences ]
    lengths = [ len(_)+1 for _ in sentences ]
    total_length = sum(lengths)
    cumsum = np.cumsum(lengths)
    step = n_chars_per_group - n_chars_overlap

    start_prev, end_prev = -1, 999999

    for char_offset in range(0, total_length, step):
        # Find the first sentence that starts after the offset
        i_start = np.argmin(cumsum < char_offset)
        # Find the first sentence that ends after the offset + n_chars_per_group
        i_end = np.argmax(char_offset + n_chars_per_group <= cumsum)

        # If no sentence ends after the offset + n_chars_per_group, take all sentences from i_start
        if i_end == 0: i_end = len(sentences)
        # Ensure that no sentence is skipped
        if end_prev < i_start: i_start = end_prev
        # Ensure that no two chunks start at the same sentence, thus avoiding duplicate chunks
        if i_start <= start_prev: i_start = start_prev + 1
        # Ensure that the start and end are not the same
        if i_start == i_end: continue
        
        start_prev = i_start
        end_prev = i_end

        # Create and store chunk
        chunk_start = int(cumsum[i_start] - lengths[i_start])
        chunk_end = int(cumsum[i_end-1])
        chunk_text = " ".join(sentences[i_start:i_end]) + " "
        chunks.append(ParagraphChunk(paragraph, chunk_text, len(chunks), chunk_start, chunk_end))
        
        # print(f"Added chunk {len(chunks):2} with {len(chunk_text):4} characters, from sentence {i_start} to {i_end-1} ({cumsum[i_start]-lengths[i_start]} to {cumsum[i_end-1]}). '{chunk_text[:20]}' ... '{chunk_text[-20:]}'") 

        # If the last chunk is less than 33% of the desired length, merge it with the previous chunk
        if 1 < len(chunks) and len(chunks[-1].text) < n_chars_per_group * 0.33:
            # print(f"Merging last chunk with previous chunk")
            chunks[-2].text = chunks[-2].text[:chunks[-1].start-chunks[-2].start] + chunks[-1].text
            chunks[-2].end = chunks[-1].end
            chunks = chunks[:-1]

        # If the last sentence is included in this chunk, break. Any other chunks would just be a subset of this last chunk
        if i_end == len(sentences): break


    return chunks

# text = """To eliminate this issue, we modified the crossbar into three different components 
# while maintaining the original length of the dribbler, as shown in Figure
# 2. We 3D printed the two crossbars and water-jetted the motor mount plate using 
# aluminium to mitigate unnecessary vibrations and potential warping during
# gameplay. The extruded cable holders on the rear-face of the crossbar have been
# rotated 90 degrees, and shifted to the top ledge of the crossbar. In addition, the
# bottom edges at the entrance of the cable holders have been chamfered by 3mm
# at 45 degrees to prevent sharp edges from cutting into the cables. With these
# modifications, it allowed us to shift the motor and dribbler gears into the interior 
# of the left dribbler plate. As a result, we are now able to connect the PCB
# wires directly to the control board without the possibility of them impeding the
# dribbler gears. The new design can be seen in Figure 2 above."""

# embeddor.embed_sparse_pinecone_bm25(text, enable_ngram=False)
# exit()


# Query = distance resolution
# !!! soccer_smallsize__2011__RoboJackets__0

papers = [
    "soccer_smallsize__2011__RoboJackets__0",
    "soccer_midsize__2019__Cambada__0",
    "soccer_midsize__2020__Cambada__0",
    "soccer_midsize__2008__Cambada__0",
    "soccer_smallsize__2020__Warthog_Robotics__0",
    "soccer_smallsize__2015__UBC_Thunderbots__0",
    "soccer_midsize__2023__LAR__0"
]


# vector_client.delete_items()
# exit()

n_items = vector_client.count_items()
print(f"n_items: {n_items}")

if n_items == 0:
    p_c = []
    for paper in papers:
        chunks = []
        paragraphs = get_paragraphs(paper)
        print(f"n_paragraphs: {len(paragraphs)}")
        for p in paragraphs:
            chunks += create_paragraph_chunks(p, 1000, 200)
        p_c.append((paper, chunks))

    for paper, chunks in p_c:
        print(f"{paper:<40} {len(paragraphs)}")
        lengths = [ len(_.text) for _ in chunks ]
        print(sorted(lengths))

    vector_client.delete_items()

    for paper, chunks in p_c:
        for i, c in enumerate(chunks):
            c:ParagraphChunk = c
            
            sparse_1gram, word_freq_1gram = embeddor.embed_sparse_pinecone_bm25(c.text, enable_ngram=False)
            sparse_2gram, word_freq_2gram = embeddor.embed_sparse_pinecone_bm25(c.text, enable_ngram=True)
            dense = embeddor.embed_dense_openai(c.text)

            vector_client.store_item(f"{paper}__{c.paragraph_sequence_id}__{c.sequence_id}__ngram_1gram", dense, sparse_1gram, {'text': c.text})
            vector_client.store_item(f"{paper}__{c.paragraph_sequence_id}__{c.sequence_id}__ngram_2gram", dense, sparse_2gram, {'text': c.text})

time.sleep(2)

query = "distance resolution"
dense_vector = embeddor.embed_dense_openai(query)
sparse_vector_query, keywords = embeddor.embed_sparse_pinecone_bm25(query, is_query=True, enable_ngram=True)
keywords = [ _ for _ in keywords.keys() if 0.1 < keywords[_] ]

print(f"Keywords: {keywords}")

items = vector_client.query_items(dense_vector, sparse_vector_query)

# texts = [ item['metadata']['text'] for item in items['matches'] ]
# texts = list(set(texts))
# for text in texts:
#     print("\n")
#     print(text)
# print()

for item in items['matches']:
    if "2gram" in item['id']:
        text = item['metadata']['text']
        print(f"{item['id']:>80}", item['score'], text[:100])


# print(keywords)
