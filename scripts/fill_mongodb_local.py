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

# weaviate_client = WeaviateClient.default_client()
# weaviate_client.reset_everything()

file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
# metadata_client:MongoDBClient = MongoDBClient("mongodb://localhost:27017/")

# metadata_client.drop_tdps()
# metadata_client.drop_paragraphs()

pdfs:list[TDPName] = file_client.list_pdfs()

# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]
pdfs = [ _ for _ in pdfs if "rescue_robot" not in _.filename.lower() ]

print(f"Found {len(pdfs)} PDFs")

total_tokens:int = 0
total_n_tokens = []
total_n_characters = []
n_max_paragraph_characters = 0
paper_max_paragraph_characters = 0


paragraphs = {}


for i_pdf, pdf in enumerate(pdfs):
    print("\n\n\n")
    print(f"Processing PDF {i_pdf+1:3}/{len(pdfs)} : {pdf}")
    pdf_filepath = file_client.get_pdf(pdf, no_copy=True)
    pdf_filehash = file_client.get_pdf_hash(pdf)
    try:
        tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)
    except Exception as e:
        logger.error(f"Error processing PDF {pdf}: {e}")
        continue

    tdp = TDP(tdp_name=pdf, filehash=pdf_filehash, structure=tdp_structure)
    tdp.propagate_information()


    for paragraph in tdp.structure.paragraphs:
        print(f"Paragraph title: {paragraph.text_raw:30} {len(paragraph.content_raw().split(' ')):3} words {len(paragraph.content_processed()):5} characters")
        # print(f"Paragraph content: '{paragraph.content_raw()}'")

        n_tokens = embeddor.count_tokens(paragraph.content_raw())
        costs = embeddor.get_price_per_token("text-embedding-3-small") * n_tokens
        
        total_tokens += n_tokens
        total_n_tokens.append(n_tokens)
        total_n_characters.append(len(paragraph.content_processed()))

        if len(paragraph.content_processed()) > n_max_paragraph_characters:
            n_max_paragraph_characters = len(paragraph.content_processed())
            paper_max_paragraph_characters = pdf

        # print(f"Costs: {costs:.2f}")

        # text = paragraph.text_processed + " " + paragraph.content_processed()
        # embedding = embeddor.embed_using_openai(text, model="text-embedding-3-small")
        # weaviate_client.store_paragraph(paragraph, embedding)

        if pdf not in paragraphs:
            paragraphs[pdf] = {
                "pdf": pdf,
                "paragraph_sizes_titles": [],
                "n_paragraphs": 0,
                "longest_paragraph": 0,
                "shortest_paragraph": 1e6
            }

        paragraphs[pdf]['paragraph_sizes_titles'].append([paragraph.content_raw(), paragraph.text_raw])
        paragraphs[pdf]['n_paragraphs'] += 1
        paragraphs[pdf]['longest_paragraph'] = max(paragraphs[pdf]['longest_paragraph'], len(paragraph.content_raw()))
        paragraphs[pdf]['shortest_paragraph'] = min(paragraphs[pdf]['shortest_paragraph'], len(paragraph.content_raw()))

    continue
    print(tdp_structure.outline())

    tdp = TDP(tdp_name=pdf, filehash=pdf_filehash, structure=tdp_structure)
    tdp.propagate_information()

    metadata_client.insert_tdp(tdp)

    for paragraph in tdp.structure.paragraphs:
        metadata_client.insert_paragraph(paragraph)


# weaviate_client.search_paragraphs_by_embedding(embedding, limit=5)

# print(f"Total tokens: {total_tokens}")
# print(f"Total costs for text-embedding-3-small: {total_tokens * embeddor.get_price_per_token('text-embedding-3-small'):.2f}")
# print(f"Total costs for     gpt-3.5-turbo-0125: {total_tokens * embeddor.get_price_per_token('gpt-3.5-turbo-0125'):.2f}")
# print(f"Total costs for                  gpt-4: {total_tokens * embeddor.get_price_per_token('gpt-4'):.2f}")
# print(f"Total costs for                 gpt-4o: {total_tokens * embeddor.get_price_per_token('gpt-4o'):.2f}")


print("\n\n\n")


largest_paragraph = sorted(paragraphs.values(), key=lambda p: p['longest_paragraph'], reverse=True)
largest_tdp = sorted(paragraphs.values(), key=lambda p: sum([len(p[0]) for p in p['paragraph_sizes_titles']]), reverse=True)
most_paragraphs = sorted(paragraphs.values(), key=lambda p: p['n_paragraphs'], reverse=True)


for theset in [largest_paragraph, largest_tdp]:
    for l in theset[:5]:
        print()
        print(l['pdf'])
        n_total = sum([len(p[0]) for p in l['paragraph_sizes_titles']])
        print(f"  Total {n_total:6}  |  n paragraphs: {l['n_paragraphs']:4}  |  longest: {l['longest_paragraph']:4}  |  shortest: {l['shortest_paragraph']:4}")

        p_sorted = sorted(l['paragraph_sizes_titles'], key=lambda p: len(p[0]), reverse=True)
        for p in p_sorted[:3]:
            print(f"    {len(p[0]):4} {p[1]}")

    print("\n==============================\n")

for theset in [most_paragraphs]:
    for l in theset[:5]:
        print()
        print(l['pdf'])
        n_total = sum([len(p[0]) for p in l['paragraph_sizes_titles']])
        print(f"  Total {n_total:6}  |  n paragraphs: {l['n_paragraphs']:4}  |  longest: {l['longest_paragraph']:4}  |  shortest: {l['shortest_paragraph']:4}")

        p_sorted = sorted(l['paragraph_sizes_titles'], key=lambda p: len(p[0]), reverse=True)
        for p in p_sorted:
            print(f"    {len(p[0]):4} {p[1]}")

    print("\n==============================\n")


exit()

print(f"Average tokens per paragraph: {total_tokens / len(total_n_tokens)}")
print(f"Median tokens per paragraph: {sorted(total_n_tokens)[len(total_n_tokens)//2]}")
print(f"Max tokens per paragraph: {max(total_n_tokens)}")
print(f"Min tokens per paragraph: {min(total_n_tokens)}")

print(f"Average characters per paragraph: {sum(total_n_characters) / len(total_n_characters)}")
print(f"Median characters per paragraph: {sorted(total_n_characters)[len(total_n_characters)//2]}")
print(f"Max characters per paragraph: {max(total_n_characters)}")
print(f"Min characters per paragraph: {min(total_n_characters)}")

print(paper_max_paragraph_characters)

# from collections import Counter
# print(Counter(total_n_tokens).most_common(10))