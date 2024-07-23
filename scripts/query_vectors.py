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
from data_access.vector.vector_filter import VectorFilter
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.TDPName import TDPName
from embedding.Embeddings import instance as embeddor
from search import search, llm
from text_processing.text_processing import reconstruct_paragraph_text
from openai import RateLimitError

vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))
llm_client = OpenAIClient()

print(f"Paragraphs: {vector_client.count_paragraphs()}    Questions: {vector_client.count_questions()}")

while True:
    print("\n\n")
    query = input("Enter query: ")
    print()
    if query == "": continue

    filter = VectorFilter(
        year_min=2015,
        leagues=["soccer_smallsize"]
    )

    try:
        paragraphs, keywords = search(vector_client, query, filter)
    except RateLimitError as e:
        print("Rate limit error! Send more money to OpenAI!")
        continue

    # text_in, text_out = llm(vector_client, query, filter, model="gpt-3.5-turbo")
    text_in, text_out = llm(vector_client, query, filter, model="gpt-4o-mini")

    print(text_out)
