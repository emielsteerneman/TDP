# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json
# Third party libraries
from custom_dotenv import load_dotenv
load_dotenv()
import numpy as np
# Local libraries
from blacklist import blacklist
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import LocalFileClient
from data_access.llm.llm_client import OpenAIClient
# from data_access.vector.weaviate_client import WeaviateClient
from data_access.vector.pinecone_client import PineconeClient
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.TDPName import TDPName
from data_structures.TDP import TDP
from data_structures.TDPStructure import TDPStructure
from embedding.Embeddings import instance as embeddor
from extraction import extractor
from MyLogger import logger



sem1 = embeddor.embed_sparse_milvus_splade("This is a test test2 bangbang")
sem2 = embeddor.embed_sparse_pinecone_bm25("This is a test test2 bangbang")

print(type(sem1), "\n", sem1)
print(type(sem2), "\n", sem2)

exit()

PATH = "/home/emiel/Desktop/projects/tdp/static/pdf/"

# weaviate_client = WeaviateClient.default_client()
# weaviate_client.reset_everything()

file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
# metadata_client:MongoDBClient = MongoDBClient("mongodb://localhost:27017/")
vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))
llm_client = OpenAIClient()

pdfs:list[TDPName] = file_client.list_pdfs()

# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]
pdfs = [ _ for _ in pdfs if "rescue_robot" not in _.filename.lower() ]
pdfs = [ _ for _ in pdfs if "soccer_smallsize" in _.filename.lower() ]
# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]
# pdfs = [ _ for _ in pdfs if "soccer_smallsize__2010__ODENS__0" in _.filename ]

# now pick a random subset of the pdfs
# pdfs = np.random.choice(pdfs, 10, replace=False)

print(f"Found {len(pdfs)} PDFs")

n_exceptions = 0
total_n_tokens = []
n_max_paragraph_tokens = 0
paper_max_paragraph_tokens = 0

def reconstruct_paragraph_text(chunks:list[ParagraphChunk]) -> str:
    reconstructed_text = ""
    starts = [ _.start for _ in chunks ]
    start_pairs = list(zip(starts, starts[1:]))
    for chunk, (start, stop) in zip(chunks, start_pairs):
        length = stop - start
        reconstructed_text += chunk.text[:length]
        # print(f"    '{chunk.text[:20]}' ... '{chunk.text[-20:]}'")
        # print(f" -> '{reconstructed_text[:20]}' ... '{reconstructed_text[-20:]}'")

    reconstructed_text += chunks[-1].text
    return reconstructed_text.strip()

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

n_chunks_stored = 0
n_questions_specific_stored = 0
n_questions_generic_stored = 0

print(f"Paragraphs: {vector_client.count_paragraphs()}    Questions: {vector_client.count_questions()}")
if vector_client.count_paragraphs() > 0 or vector_client.count_questions() > 0:
    confirmation = input(f"Are you sure you want to process {len(pdfs)} PDFs? (y/n): ")
    if confirmation.lower() != "y":
        print("Exiting")
        exit()

# vector_client.delete_paragraphs()
# vector_client.delete_questions()

# metadata_client.drop_tdps()
# metadata_client.drop_paragraphs()

ef = milvus_model.DefaultEmbeddingFunction()
print(ef)
exit()

for i_pdf, pdf in enumerate(pdfs):
    
    ### Load
    if pdf.filename in blacklist: continue
    print(f"\n\n\nProcessing PDF {i_pdf+1:3}/{len(pdfs)} : {pdf}")
    pdf_filepath = file_client.get_pdf(pdf, no_copy=True)
    pdf_filehash = file_client.get_pdf_hash(pdf)

    ### Parse
    try:
        tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)
    except Exception as e:
        logger.error(f"Error processing PDF {pdf}: {e}")
        n_exceptions += 1
        continue

    tdp = TDP(tdp_name=pdf, filehash=pdf_filehash, structure=tdp_structure)
    tdp.propagate_information()

    ### Process each paragraph
    for paragraph in tdp.structure.paragraphs:

        n_tokens = embeddor.count_tokens(paragraph.content_raw())
        n_chars = len(paragraph.content_raw())

        if n_chars < 10: 
            print(f"    {paragraph.text_raw:50} {n_tokens:4} tokens    {n_chars:5} chars   SKIPPING")
            continue

        paragraph_chunks:list[ParagraphChunk] = create_paragraph_chunks(paragraph, n_chars_per_group=2000, n_chars_overlap=500)

        print(f"    {paragraph.text_raw:50} {n_tokens:4} tokens    {n_chars:5} chars    {len(paragraph_chunks):2} chunks   {n_chars/n_tokens:.2f} chars/token", [ len(_.text) for _ in paragraph_chunks ])

        # Reconstruct the paragraph from the chunks
        reconstructed_text = reconstruct_paragraph_text(paragraph_chunks)
        if paragraph.content_raw() != reconstructed_text:
            print("!!!!!!!!!!\nParagraph content raw\n")
            print(paragraph.content_raw())
            print("\nreconstructed text\n")
            print(reconstructed_text)
            print("\n\n")
            raise Exception("Reconstruction failed")

        for i_chunk, chunk in enumerate(paragraph_chunks):
            pass

        continue

        for i_chunk, chunk in enumerate(paragraph_chunks):
            dense_embedding = embeddor.embed_using_openai(chunk.text, model="text-embedding-3-small")
            sparse_embedding = embeddor.sparse_embed_using_bm25(chunk.text)
            vector_client.store_paragraph_chunk(chunk, dense_embedding, sparse_embedding)
            n_chunks_stored += 1

            n_questions = len(chunk.text) // 500
            if 0 < n_questions:
                response_obj = llm_client.generate_paragraph_chunk_information(chunk, n_questions)
                # print(chunk.text)
                # print(json.dumps(response_obj, indent=4))

                if 'questions_specific' in response_obj:
                    for question in response_obj['questions_specific']:
                        # print(f"        S? {question}")
                        dense_embedding = embeddor.embed_using_openai(question, model="text-embedding-3-small")
                        sparse_embedding = embeddor.sparse_embed_using_bm25(question)
                        vector_client.store_question(chunk, question, dense_embedding, sparse_embedding)
                        n_questions_specific_stored += 1
                if 'questions_generic' in response_obj:
                    for question in response_obj['questions_generic']:
                        # print(f"        G? {question}")
                        dense_embedding = embeddor.embed_using_openai(question, model="text-embedding-3-small")
                        sparse_embedding = embeddor.sparse_embed_using_bm25(question)
                        vector_client.store_question(chunk, question, dense_embedding, sparse_embedding)
                        n_questions_generic_stored += 1

    print(f"Current costs: {embeddor.total_costs + llm_client.total_costs:.2f} (Embeddings: {embeddor.total_costs:.2f}  LLM: {llm_client.total_costs:.2f})")

        ### Statistics
        
        
        # total_n_tokens.append(n_tokens)
        # if n_max_paragraph_tokens < n_tokens:
        #     n_max_paragraph_tokens = n_tokens
        #     paper_max_paragraph_tokens = pdf

        # if pdf not in paragraphs:
        #     paragraphs[pdf] = {
        #         "pdf": pdf,
        #         "paragraph_sizes_titles": [],
        #         "n_paragraphs": 0,
        #         "n_tokens": 0,
        #         "longest_paragraph": 0,
        #         "shortest_paragraph": 1e6
        #     }
        # paragraphs[pdf]['paragraph_sizes_titles'].append([n_tokens, paragraph.text_raw])
        # paragraphs[pdf]['n_paragraphs'] += 1
        # paragraphs[pdf]['n_tokens'] += n_tokens
        # paragraphs[pdf]['longest_paragraph'] = max(paragraphs[pdf]['longest_paragraph'], n_tokens)
        # paragraphs[pdf]['shortest_paragraph'] = min(paragraphs[pdf]['shortest_paragraph'], n_tokens)

print("\n\n\n")
for pdf in pdfs: print(pdf.filename)
print("\n")

print(f"Stored {n_chunks_stored} chunks over {len(pdfs)} PDFs")
print(f"Stored {n_questions_specific_stored} specific questions")
print(f"Stored {n_questions_generic_stored} generic questions")

# weaviate_client.search_paragraphs_by_embedding(embedding, limit=5)

# print("\n\n\n\n")
# total_tokens = sum(total_n_tokens)
# print(f"Total tokens: {total_tokens}")
# print(f"Total costs for text-embedding-3-small: {total_tokens * embeddor.get_price_per_token('text-embedding-3-small'):.2f}")
# print(f"Total costs for     gpt-3.5-turbo-0125: {total_tokens * embeddor.get_price_per_token('gpt-3.5-turbo-0125'):.2f}")
# print(f"Total costs for                  gpt-4: {total_tokens * embeddor.get_price_per_token('gpt-4'):.2f}")
# print(f"Total costs for                 gpt-4o: {total_tokens * embeddor.get_price_per_token('gpt-4o'):.2f}")

# print("\n\n\n\n")

# largest_paragraph = sorted(paragraphs.values(), key=lambda p: p['longest_paragraph'], reverse=True)
# largest_tdp = sorted(paragraphs.values(), key=lambda p: p['n_tokens'], reverse=True)
# most_paragraphs = sorted(paragraphs.values(), key=lambda p: p['n_paragraphs'], reverse=True)


# for theset in [largest_paragraph, largest_tdp]:
#     for l in theset[:3]:
#         print()
#         print(PATH + l['pdf'].to_filepath())
#         print(f"  n tokens {l['n_tokens']:6}  |  n paragraphs: {l['n_paragraphs']:4}  |  longest: {l['longest_paragraph']:4}  |  shortest: {l['shortest_paragraph']:4}")

#         p_sorted = sorted(l['paragraph_sizes_titles'], key=lambda p: p[0], reverse=True)
#         for p in p_sorted[:3]:
#             print(f"    {p[0]:4} {p[1]}")

#     print("\n==============================\n")

# for theset in [most_paragraphs]:
#     for l in theset[:3]:
#         print()
#         print(PATH + l['pdf'].to_filepath())
#         print(f"  n tokens {l['n_tokens']:6}  |  n paragraphs: {l['n_paragraphs']:4}  |  longest: {l['longest_paragraph']:4}  |  shortest: {l['shortest_paragraph']:4}")

#         p_sorted = sorted(l['paragraph_sizes_titles'], key=lambda p: p[0], reverse=True)
#         for p in p_sorted:
#             print(f"    {p[0]:4} {p[1]}")

#     print("\n==============================\n")

# print(f"Number of exceptions: {n_exceptions}")

# total_n_tokens = [ _ for _ in total_n_tokens if 0 < _ ]
# print(f"Median tokens per paragraph: {sorted(total_n_tokens)[len(total_n_tokens)//2]}")
# print(f"Average tokens per paragraph: {total_tokens / len(total_n_tokens)}")
# print(f"Std dev tokens per paragraph: {np.std(total_n_tokens)}")
# print(f"Max tokens per paragraph: {max(total_n_tokens)}")
# print(f"Min tokens per paragraph: {min(total_n_tokens)}")


# # Plot histogram of paragraph token sizes
# import seaborn as sns
# import matplotlib.pyplot as plt
# total_n_tokens_notzero = [ min(1500, _) for _ in total_n_tokens if _ > 0 ]


# nonzero_sorted = sorted(total_n_tokens_notzero)
# # for 10%, 20%, 30% etc, print the value
# for i in range(1, 10):
#     print(f"{i*10}%: {nonzero_sorted[len(nonzero_sorted)*i//10]}")

# sns.histplot(total_n_tokens_notzero, bins=100)
# plt.show()

# # from collections import Counter
# # print(Counter(total_n_tokens).most_common(10))