# System libraries
import os
# Third party libraries
import numpy as np
from openai import OpenAI
from pinecone_text.sparse import BM25Encoder
# import pymilvus
# import pymilvus.model
from scipy.sparse import csr_matrix, coo_array
import tiktoken
# Local libraries
from MyLogger import logger

class Embeddor:

    # Costs per token
    api_costs = {
        "text-embedding-3-small": {
            "input": 0.02 / 1e6
        },
        "text-embedding-3-large": {
            "input": 0.13 / 1e6
        }
    }

    def __init__(self):
        self.model = None
        self.openai_client = None
        self.sparse_pinecone_bm25 = None
        self.dense_milvus = None
        self.sparse_milvus_splade = None
        self.total_costs = 0

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def embed_using_sentence_transformer(self, text:str | list[str]) -> np.ndarray:
        if self.model is None:
            self.load_sentence_transformer()
        return self.model.encode(text)

    def embed_dense_openai(self, text:str | list[str], model="text-embedding-3-small") -> np.ndarray:
        if self.openai_client is None:
            self.load_openai_client()
        
        is_str:bool = isinstance(text, str)

        if is_str: 
            response = self.openai_client.embeddings.create(input = [text], model=model)
            self.total_costs += response.usage.prompt_tokens * self.api_costs[response.model]["input"]            
            return np.array(response.data[0].embedding)
        else:
            response = self.openai_client.embeddings.create(input = text, model=model)
            self.total_costs += response.usage.prompt_tokens * self.api_costs[response.model]["input"]
            return np.array([ _.embedding for _ in response.data ])

    def embed_dense_milvus(self, text:str | list[str]) -> np.ndarray:
        # https://milvus.io/api-reference/pymilvus/v2.4.x/EmbeddingModels/SentenceTransformerEmbeddingFunction/SentenceTransformerEmbeddingFunction.md
        if self.dense_milvus is None:
            self.dense_milvus = pymilvus.model.dense.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2",
                device="cpu"
            )

        is_str:bool = isinstance(text, str)

        if is_str:
            return self.dense_milvus.encode_documents([text])[0]
        else:
            return self.dense_milvus.encode_documents(text)

    def embed_sparse_milvus_splade(self, text:str | list[str], is_query:bool=False) -> coo_array:
        # https://milvus.io/api-reference/pymilvus/v2.4.x/EmbeddingModels/SpladeEmbeddingFunction/SpladeEmbeddingFunction.md
        if self.sparse_milvus_splade is None:
            self.sparse_milvus_splade = pymilvus.model.sparse.SpladeEmbeddingFunction(
                model_name="naver/splade-cocondenser-ensembledistil",
                device="cpu"
            )            
            
        is_str:bool = isinstance(text, str)

        if is_str:
            if is_query:
                result:csr_matrix = self.sparse_milvus_splade.encode_queries([text])
            else:
                result:csr_matrix = self.sparse_milvus_splade.encode_documents([text])
            return coo_array(result)
        else:
            raise NotImplementedError("Batch encoding not implemented yet")

    def embed_sparse_pinecone_bm25(self, text:str | list[str], is_query:bool=False) -> coo_array:
        if self.sparse_pinecone_bm25 is None:
            self.sparse_pinecone_bm25 = self.load_default_bm25_encoder()
            
        is_str:bool = isinstance(text, str)

        if is_str:
            if is_query:
                sparse_dict = self.sparse_pinecone_bm25.encode_queries(text)
            else:
                sparse_dict = self.sparse_pinecone_bm25.encode_documents(text)
            return coo_array( (sparse_dict['values'], (np.zeros(len(sparse_dict['indices']),dtype=int), sparse_dict['indices']) ) )
        else:
            raise NotImplementedError("Batch encoding not implemented yet")

    def preprocess_using_bm25(self, text:str) -> str:
        if self.sparse_pinecone_bm25 is None:
            self.sparse_pinecone_bm25 = self.load_default_bm25_encoder()

        return " ".join(self.sparse_pinecone_bm25._tokenizer(text))

    def load_default_bm25_encoder(self) -> BM25Encoder:
        logger.info("Loading default BM25 encoder")
        """Create a BM25 model from pre-made params for the MS MARCO passages corpus"""
        bm25 = BM25Encoder()
        url = "https://storage.googleapis.com/pinecone-datasets-dev/bm25_params/msmarco_bm25_params_v4_0_0.json"
        filepath = "msmarco_bm25_params_v4_0_0.json"
        if not os.path.exists(filepath):
            logger.info(f"Downloading BM25 params from {url}")
            import wget
            wget.download(url, filepath)
        bm25.load(filepath)
        return bm25

    def count_tokens(self, text:str, encoding:str="cl100k_base") -> int:
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        return len(tiktoken.get_encoding(encoding).encode(text))
    
    def get_price_per_token(self, model:str="text-embedding-3-small") -> float:
        """
        Model                       Dollar / 1M tokens
        text-embedding-3-small      $0.02
        text-embedding-3-large      $0.13
        text-embedding-ada-002      $0.10
        gpt-3.5-turbo-0125          $0.50
        gpt-4                       $30.00
        gpt-4-turbo                 $10.00
        gpt-4o                      $5.00   
        """
        if model == "text-embedding-3-small": return 0.02 / 1e6
        if model == "text-embedding-3-large": return 0.13 / 1e6
        if model == "text-embedding-ada-002": return 0.10 / 1e6
        if model == "gpt-3.5-turbo-0125": return 0.50 / 1e6
        if model == "gpt-4": return 30.00 / 1e6
        if model == "gpt-4-turbo": return 10.00 / 1e6
        if model == "gpt-4o": return 5.00 / 1e6

    def load_sentence_transformer(self) -> None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading model 'sentence-transformers/all-mpnet-base-v2'")
        self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
        logger.info("Model loaded")
    
    def load_openai_client(self) -> None:
        self.openai_client = OpenAI()
        logger.info("OpenAI client loaded")

instance = Embeddor()