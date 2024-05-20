# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Third party libraries
from custom_dotenv import load_dotenv
load_dotenv()
import numpy as np
# Local libraries
from blacklist import blacklist
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import LocalFileClient
from data_access.vector.weaviate_client import WeaviateClient
from data_structures.TDPName import TDPName
from data_structures.TDP import TDP
from data_structures.TDPStructure import TDPStructure
from embedding.Embeddings import instance as embeddor
from extraction import extractor
from MyLogger import logger

PATH = "/home/emiel/Desktop/projects/tdp/static/pdf/"

weaviate_client = WeaviateClient.default_client()
weaviate_client.reset_everything()

file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
# metadata_client:MongoDBClient = MongoDBClient("mongodb://localhost:27017/")

# metadata_client.drop_tdps()
# metadata_client.drop_paragraphs()

pdfs:list[TDPName] = file_client.list_pdfs()

# pdfs = [ _ for _ in pdfs if "RoboTeam_Twente" in _.filename ]
pdfs = [ _ for _ in pdfs if "rescue_robot" not in _.filename.lower() ]
pdfs = pdfs[:15]

print(f"Found {len(pdfs)} PDFs")

n_exceptions = 0
total_tokens:int = 0
total_n_tokens = []
total_n_characters = []
n_max_paragraph_tokens = 0
paper_max_paragraph_tokens = 0


paragraphs = {}


for i_pdf, pdf in enumerate(pdfs):
    if pdf.filename in blacklist: continue
    print("\n\n\n")
    print(f"Processing PDF {i_pdf+1:3}/{len(pdfs)} : {pdf}")
    pdf_filepath = file_client.get_pdf(pdf, no_copy=True)
    pdf_filehash = file_client.get_pdf_hash(pdf)
    # tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)
    try:
        tdp_structure:TDPStructure = extractor.process_pdf(pdf_filepath)
    except Exception as e:
        logger.error(f"Error processing PDF {pdf}: {e}")
        n_exceptions += 1
        continue

    tdp = TDP(tdp_name=pdf, filehash=pdf_filehash, structure=tdp_structure)
    tdp.propagate_information()

    for paragraph in tdp.structure.paragraphs:
        print(f"    {paragraph.text_raw:50} {embeddor.count_tokens(paragraph.content_raw()):4} tokens    {len(paragraph.content_processed()):5} chars")
        # print(f"Paragraph content: '{paragraph.content_raw()}'")

        n_tokens = embeddor.count_tokens(paragraph.content_raw())
        costs = embeddor.get_price_per_token("text-embedding-3-small") * n_tokens
        
        total_tokens += n_tokens
        total_n_tokens.append(n_tokens)
        total_n_characters.append(len(paragraph.content_processed()))

        if n_max_paragraph_tokens < n_tokens:
            n_max_paragraph_tokens = n_tokens
            paper_max_paragraph_tokens = pdf

        # print(f"Costs: {costs:.2f}")

        # text = paragraph.text_processed + " " + paragraph.content_processed()
        # embedding = embeddor.embed_using_openai(text, model="text-embedding-3-small")
        # weaviate_client.store_paragraph(paragraph, embedding)

        if pdf not in paragraphs:
            paragraphs[pdf] = {
                "pdf": pdf,
                "paragraph_sizes_titles": [],
                "n_paragraphs": 0,
                "n_tokens": 0,
                "longest_paragraph": 0,
                "shortest_paragraph": 1e6
            }

        paragraphs[pdf]['paragraph_sizes_titles'].append([n_tokens, paragraph.text_raw])
        paragraphs[pdf]['n_paragraphs'] += 1
        paragraphs[pdf]['n_tokens'] += n_tokens
        paragraphs[pdf]['longest_paragraph'] = max(paragraphs[pdf]['longest_paragraph'], n_tokens)
        paragraphs[pdf]['shortest_paragraph'] = min(paragraphs[pdf]['shortest_paragraph'], n_tokens)

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


print("\n\n\n\n\n\n\n\n\n")


largest_paragraph = sorted(paragraphs.values(), key=lambda p: p['longest_paragraph'], reverse=True)
largest_tdp = sorted(paragraphs.values(), key=lambda p: p['n_tokens'], reverse=True)
most_paragraphs = sorted(paragraphs.values(), key=lambda p: p['n_paragraphs'], reverse=True)


for theset in [largest_paragraph, largest_tdp]:
    for l in theset[:3]:
        print()
        print(PATH + l['pdf'].to_filepath())
        print(f"  n tokens {l['n_tokens']:6}  |  n paragraphs: {l['n_paragraphs']:4}  |  longest: {l['longest_paragraph']:4}  |  shortest: {l['shortest_paragraph']:4}")

        p_sorted = sorted(l['paragraph_sizes_titles'], key=lambda p: p[0], reverse=True)
        for p in p_sorted[:3]:
            print(f"    {p[0]:4} {p[1]}")

    print("\n==============================\n")

for theset in [most_paragraphs]:
    for l in theset[:3]:
        print()
        print(PATH + l['pdf'].to_filepath())
        print(f"  n tokens {l['n_tokens']:6}  |  n paragraphs: {l['n_paragraphs']:4}  |  longest: {l['longest_paragraph']:4}  |  shortest: {l['shortest_paragraph']:4}")

        p_sorted = sorted(l['paragraph_sizes_titles'], key=lambda p: p[0], reverse=True)
        for p in p_sorted:
            print(f"    {p[0]:4} {p[1]}")

    print("\n==============================\n")

print(f"Number of exceptions: {n_exceptions}")

total_n_tokens = [ _ for _ in total_n_tokens if 0 < _ ]
print(f"Median tokens per paragraph: {sorted(total_n_tokens)[len(total_n_tokens)//2]}")
print(f"Average tokens per paragraph: {total_tokens / len(total_n_tokens)}")
print(f"Std dev tokens per paragraph: {np.std(total_n_tokens)}")
print(f"Max tokens per paragraph: {max(total_n_tokens)}")
print(f"Min tokens per paragraph: {min(total_n_tokens)}")

# print(f"Median characters per paragraph: {sorted(total_n_characters)[len(total_n_characters)//2]}")
# print(f"Average characters per paragraph: {sum(total_n_characters) / len(total_n_characters)}")
# print(f"Max characters per paragraph: {max(total_n_characters)}")
# print(f"Min characters per paragraph: {min(total_n_characters)}")

# Plot histogram of paragraph token sizes
import seaborn as sns
import matplotlib.pyplot as plt
total_n_tokens_notzero = [ min(1500, _) for _ in total_n_tokens if _ > 0 ]


nonzero_sorted = sorted(total_n_tokens_notzero)
# for 10%, 20%, 30% etc, print the value
for i in range(1, 10):
    print(f"{i*10}%: {nonzero_sorted[len(nonzero_sorted)*i//10]}")

sns.histplot(total_n_tokens_notzero, bins=100)
plt.show()

# from collections import Counter
# print(Counter(total_n_tokens).most_common(10))