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

