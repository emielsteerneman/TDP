# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json
# Third party libraries
from dotenv import load_dotenv
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
from data_structures.ProcessStateEnum import ProcessStateEnum
from data_structures.TDPName import TDPName
from data_structures.TDP import TDP
from data_structures.TDPStructure import TDPStructure
from embedding.Embeddings import instance as embeddor
from extraction import extractor
from MyLogger import logger
from simple_profiler import SimpleProfiler
from text_processing.text_processing import reconstruct_paragraph_text

# sem1 = embeddor.embed_sparse_milvus_splade("This is a test test2 bangbang")
# sem2 = embeddor.embed_sparse_pinecone_bm25("This is a test test2 bangbang")

# print(type(sem1), "\n", sem1)
# print(type(sem2), "\n", sem2)

PATH = "/home/emiel/Desktop/projects/tdp/static/pdf/"

# weaviate_client = WeaviateClient.default_client()
# weaviate_client.reset_everything()

file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
metadata_client:MongoDBClient = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))
llm_client = OpenAIClient()

profiler = SimpleProfiler()

pdfs:list[TDPName] = file_client.list_pdfs()[0]

# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]
pdfs = [ _ for _ in pdfs if "rescue_robot" not in _.filename.lower() ]
# pdfs = [ _ for _ in pdfs if "soccer_smallsize" not in _.filename.lower() ]
# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]
# pdfs = [ _ for _ in pdfs if "soccer_smallsize__2010__ODENS__0" in _.filename ]

# pdfs = [ _ for _ in pdfs if "202" in _.filename ]

# now pick a random subset of the pdfs
# pdfs = np.random.choice(pdfs, 5, replace=False)

print(f"Found {len(pdfs)} PDFs")
# exit()

n_exceptions = 0
total_n_tokens = []
n_max_paragraph_tokens = 0
paper_max_paragraph_tokens = 0

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

print(f"Paragraphs: {vector_client.count_paragraph_chunks()}    Questions: {vector_client.count_questions()}")
if vector_client.count_paragraph_chunks() > 0 or vector_client.count_questions() > 0:
    confirmation = input(f"Are you sure you want to process {len(pdfs)} PDFs? (y/n): ")
    if confirmation.lower() != "y":
        print("Exiting")
        exit()

# vector_client.delete_paragraph_chunks()
# vector_client.delete_questions()

# metadata_client.drop_tdps()
# metadata_client.drop_paragraphs()

for i_pdf, tdp_name in enumerate(pdfs):
    try:
        ### Load
        if tdp_name.filename in blacklist: continue
        print(f"\n\n\nProcessing PDF {i_pdf+1:3}/{len(pdfs)} : {tdp_name}")
        profiler.start("load pdf and hash")
        pdf_filepath = file_client.get_pdf(tdp_name, no_copy=True)
        pdf_filehash = file_client.get_filehash(tdp_name)
        profiler.stop()

        profiler.start("find tdp in metadata")
        tdp_db = metadata_client.find_tdp_by_name(tdp_name)
        profiler.stop()

        if tdp_db is not None:
            # Already processed. Skip
            if tdp_db.state['process_state'] == ProcessStateEnum.COMPLETED:
                print(f"Already processed {tdp_name}")
                continue
            
            # Somehow not completed. Remove and reprocess
            profiler.start("delete from database")
            error = False
            error |= vector_client.delete_paragraph_chunks_by_tdpname(tdp_name)
            error |= vector_client.delete_questions_by_tdpname(tdp_name)
            if not error: metadata_client.delete_tdp_by_name(tdp_name)
            profiler.stop()
            print(f"Reprocessing {tdp_name}. State={tdp_db.state['process_state']}. Error={tdp_db.state['error']}")

        ### Parse
        try:
            profiler.start("process pdf")
            tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)
            profiler.stop()
        except Exception as e:
            logger.error(f"Error processing PDF {tdp_name}: {e}")
            n_exceptions += 1
            continue

        tdp = TDP(tdp_name=tdp_name, filehash=pdf_filehash, structure=tdp_structure, process_state=ProcessStateEnum.IN_PROGRESS)
        tdp.propagate_information()

        ### Store in metadata
        profiler.start("insert metadata")
        metadata_client.insert_tdp(tdp)
        profiler.stop()

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
                profiler.start("embed dense openai")
                dense_embedding = embeddor.embed_dense_openai(chunk.text, model="text-embedding-3-small")
                profiler.start("embed sparse pinecone")
                sparse_embedding, _ = embeddor.embed_sparse_pinecone_bm25(chunk.text)
                profiler.start("store paragraph chunk")
                vector_client.store_paragraph_chunk(chunk, dense_embedding, sparse_embedding)
                profiler.stop()
                n_chunks_stored += 1

                n_questions = len(chunk.text) // 500
                if 0 < n_questions:
                    profiler.start("generate paragraph chunk info")
                    response_obj = llm_client.generate_paragraph_chunk_information(chunk, n_questions)
                    profiler.stop()
                    # print(chunk.text)
                    # print(json.dumps(response_obj, indent=4))

                    if 'questions_specific' in response_obj:
                        for question in response_obj['questions_specific']:
                            # print(f"        S? {question}")
                            profiler.start("embed dense openai")
                            dense_embedding = embeddor.embed_dense_openai(question, model="text-embedding-3-small")
                            profiler.start("embed sparse pinecone")
                            sparse_embedding, _ = embeddor.embed_sparse_pinecone_bm25(question)
                            profiler.start("store question")
                            vector_client.store_question(chunk, question, dense_embedding, sparse_embedding)
                            profiler.stop()
                            n_questions_specific_stored += 1
                    if 'questions_generic' in response_obj:
                        for question in response_obj['questions_generic']:
                            # print(f"        G? {question}")
                            profiler.start("embed dense openai")
                            dense_embedding = embeddor.embed_dense_openai(question, model="text-embedding-3-small")
                            profiler.start("embed sparse pinecone")
                            sparse_embedding, _ = embeddor.embed_sparse_pinecone_bm25(question)
                            profiler.start("store question")
                            vector_client.store_question(chunk, question, dense_embedding, sparse_embedding)
                            profiler.stop()
                            n_questions_generic_stored += 1

        profiler.start("update tdp process state")
        metadata_client.update_tdp_process_state(tdp_name, ProcessStateEnum.COMPLETED)
        profiler.stop()
        print(f"Current costs: {embeddor.total_costs + llm_client.total_costs:.2f} (Embeddings: {embeddor.total_costs:.2f}  LLM: {llm_client.total_costs:.2f})")
    except Exception as e:
        n_exceptions += 1
        logger.error(f"Error processing PDF {tdp_name}: {e}")
        profiler.start("update tdp process state")
        metadata_client.update_tdp_process_state(tdp_name, ProcessStateEnum.FAILED, error=str(e))
        profiler.stop()

    profiler.print_statistics()


print("\n\n\n")
for tdp_name in pdfs: print(tdp_name.filename)
print("\n")

print(f"Stored {n_chunks_stored} chunks over {len(pdfs)} PDFs")
print(f"Stored {n_questions_specific_stored} specific questions")
print(f"Stored {n_questions_generic_stored} generic questions")

print("Number of PDFS in metadata:", metadata_client.count_tdps())
