## Databases

Milvus, Pinecone, Weaviate, FAISS, QDrant, Pathway LLM, Annoy


- Articles
https://www.kdnuggets.com/an-honest-comparison-of-open-source-vector-databases
https://www.kdnuggets.com/the-5-best-vector-databases-you-must-try-in-2024
https://www.kdnuggets.com/2023/08/python-vector-databases-vector-indexes-architecting-llm-apps.html
https://www.linkedin.com/pulse/weaviate-pinecone-comparison-skitsanos/

* Should support both dense vectors and sparse vectors
* Vector DB vs Vector Index

Open Source databases:
"Milvus is renowned for its capabilities in similarity search and analytics"
"Weaviate can store both vectors and data objects, ideal for a range of search techniques (E.G. vector searches and keyword searches)."

RAG vs Semantic Search https://www.webuters.com/rag-vs-semantic-search-the-ai-techniques-redefining-data-retrieval

how-to pinecone https://app.pinecone.io/organizations/-NXe58s7Bg1lsQAZrVhr/projects/serverless:g5e26fm/indexes

## Sparse vectors
Either go with simple word indices like BM25 or mode advanced NNs like used in SPLADE
- Want to support literal keyword search, can't be done with SPLADE. 
https://medium.com/@infiniflowai/sparse-embedding-or-bm25-84c942b3eda7

## Issues to solve
### How to reduce costs !?!?

All stuff needs to be running only on-demand, like Azure Functions. So, no 24/7 VMs or Docker containers.
* Issue: Loading a neural network takes time, can't really be done on demand. So, how to generate sparse vectors?
    * Dense vectors can be generated using the OpenAI API. Should be very cheap

### Can I fit everything into a single database?
For embeddings, should support vector search (preferably dense and sparse)
Should also support TDP structures (team, year, league, etc).
Should support relational data (Sentence to TDP)

I want to 
- 1 | filter sentences on metadata (team / year / league).
This means that each sentence needs that metadata, so it's all denormalized

- 2 | Get all sentences that belong to a paragraph for RAG
This means that each sentence needs a paragraph id, and that sentences should be able to be retrieved based on paragraph id. Also, sentences should somehow be sortable. So either
  1. Store sentences like linked lists, using a value next_sentence_id
  2. Ensure that sentences can be sorted by their id / or some sequence number
  3. Create a column/table paragraph_id -> [ sentence_id ]
  4. Store paragraphs with their entire text

Option 2 is probably best, with a proper sequence_number

Denormalized Sentence:
  - TDP id, Paragraph id
  - Year/Team/League, Paragraph title+sequence