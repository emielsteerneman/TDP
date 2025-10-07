# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json
# Third party libraries
import numpy as np
# Local libraries
from blacklist import blacklist
from data_access.file.file_client import LocalFileClient
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
import startup
from text_processing.text_processing import reconstruct_paragraph_text


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
    # TODO move this function to an utilities file or something
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


file_client:LocalFileClient = startup.get_file_client()
profiler = SimpleProfiler()

pdfs:list[TDPName] = file_client.list_pdfs()[0]
logger.info(f"Found {len(pdfs)} PDFs")

n_exceptions = 0
total_n_tokens = []
n_max_paragraph_tokens = 0
paper_max_paragraph_tokens = 0

n_chunks_stored = 0
n_questions_specific_stored = 0
n_questions_generic_stored = 0

# metadata_client.drop_tdps()
# metadata_client.drop_paragraphs()

for i_pdf, tdp_name in enumerate(pdfs[:5]):
    try:
        ### Load
        if tdp_name.filename in blacklist: continue

        logger.info(f"\n\n\n\n\nProcessing PDF {i_pdf+1:3}/{len(pdfs)} : {tdp_name}")
        profiler.start("load pdf and hash")
        pdf_filepath = file_client.get_pdf(tdp_name, no_copy=True)
        pdf_filehash = file_client.get_filehash(tdp_name, ext=TDPName.PDF_EXT)
        profiler.stop()

        ### Parse
        try:
            profiler.start("process pdf")
            tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)
            duration = profiler.stop()
            logger.info(f"Processed PDF in {duration:.2f} seconds")
        except Exception as e:
            profiler.stop()
            logger.error(f"Error processing PDF {tdp_name}: {e}")
            n_exceptions += 1
            continue

        tdp = TDP(tdp_name=tdp_name, filehash=pdf_filehash, structure=tdp_structure, process_state=ProcessStateEnum.IN_PROGRESS)
        tdp.propagate_information()
        # print(tdp.structure.to_dict())
        print( json.dumps( tdp.structure.to_dict() ) )
        

    except Exception as e:
        n_exceptions += 1
        logger.error(f"Error processing PDF {tdp_name}: {e}")
        profiler.start("update tdp process state")
        profiler.stop()

    print(profiler.print_statistics())


# print("\n\n\n")
# for tdp_name in pdfs: logger.info(tdp_name.filename)
# print("\n")

logger.info(f"Stored {n_chunks_stored} chunks over {len(pdfs)} PDFs")
logger.info(f"Stored {n_questions_specific_stored} specific questions")
logger.info(f"Stored {n_questions_generic_stored} generic questions")