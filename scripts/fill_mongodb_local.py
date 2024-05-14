# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Third party libraries
from custom_dotenv import load_dotenv
load_dotenv()
# Local libraries
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import LocalFileClient
from data_access.vector.weaviate_client import WeaviateClient
from data_structures.TDPName import TDPName
from data_structures.TDP import TDP
from data_structures.TDPStructure import TDPStructure
from embedding.Embeddings import instance as embeddor
from extraction import extractor
from MyLogger import logger

weaviate_client = WeaviateClient.default_client()
weaviate_client.reset_everything()

file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
# metadata_client:MongoDBClient = MongoDBClient("mongodb://localhost:27017/")

# metadata_client.drop_tdps()
# metadata_client.drop_paragraphs()

pdfs:list[TDPName] = file_client.list_pdfs()[:1]

# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]

print(f"Found {len(pdfs)} PDFs")

total_tokens:int = 0
total_n_tokens = []

for i_pdf, pdf in enumerate(pdfs):
    print("\n\n\n")
    print(f"Processing PDF {i_pdf+1:3}/{len(pdfs)} : {pdf}")
    pdf_filepath = file_client.get_pdf(pdf, no_copy=True)
    pdf_filehash = file_client.get_pdf_hash(pdf)
    tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)

    tdp = TDP(tdp_name=pdf, filehash=pdf_filehash, structure=tdp_structure)
    tdp.propagate_information()


    for paragraph in tdp.structure.paragraphs[:6]:
        print(f"Paragraph title: {paragraph.text_raw:30} {len(paragraph.content_raw().split(' ')):3} words")
        # print(f"Paragraph content: '{paragraph.content_raw()}'")

        n_tokens = embeddor.count_tokens(paragraph.content_raw())
        costs = embeddor.get_price_per_token("text-embedding-3-small") * n_tokens
        
        total_tokens += n_tokens
        total_n_tokens.append(n_tokens)
        # print(f"Costs: {costs:.2f}")

        text = paragraph.text_processed + " " + paragraph.content_processed()
        embedding = embeddor.embed_using_openai(text, model="text-embedding-3-small")

        weaviate_client.store_paragraph(paragraph, embedding)



    continue
    print(tdp_structure.outline())

    tdp = TDP(tdp_name=pdf, filehash=pdf_filehash, structure=tdp_structure)
    tdp.propagate_information()

    metadata_client.insert_tdp(tdp)

    for paragraph in tdp.structure.paragraphs:
        metadata_client.insert_paragraph(paragraph)


weaviate_client.search_paragraphs_by_embedding(embedding, limit=5)

# print(f"Total tokens: {total_tokens}")
# print(f"Total costs for text-embedding-3-small: {total_tokens * embeddor.get_price_per_token('text-embedding-3-small'):.2f}")
# print(f"Total costs for     gpt-3.5-turbo-0125: {total_tokens * embeddor.get_price_per_token('gpt-3.5-turbo-0125'):.2f}")
# print(f"Total costs for                  gpt-4: {total_tokens * embeddor.get_price_per_token('gpt-4'):.2f}")
# print(f"Total costs for                 gpt-4o: {total_tokens * embeddor.get_price_per_token('gpt-4o'):.2f}")

# print(f"Average tokens per paragraph: {total_tokens / len(total_n_tokens)}")
# print(f"Median tokens per paragraph: {sorted(total_n_tokens)[len(total_n_tokens)//2]}")
# print(f"Max tokens per paragraph: {max(total_n_tokens)}")
# print(f"Min tokens per paragraph: {min(total_n_tokens)}")
# from collections import Counter
# print(Counter(total_n_tokens).most_common(10))