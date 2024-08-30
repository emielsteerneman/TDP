# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from collections import Counter
import json
import mmh3
# Third party libraries
import numpy as np
from openai import OpenAI, RateLimitError
from pinecone_text.sparse.bm25_tokenizer import BM25Tokenizer
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
        self.dense_milvus = None
        self.sparse_milvus_splade = None
        self.total_costs = 0

        # Tokenizers used for creating ngrams in embed_sparse_prefitted_bm25()
        self.bm25_tokenizer_stopwords = BM25Tokenizer(
            lower_case=True,
            remove_punctuation=True,
            remove_stopwords=False,
            stem=True,
            language="english"
        )
        self.bm25_tokenizer_nostopwords = BM25Tokenizer(
            lower_case=True,
            remove_punctuation=True,
            remove_stopwords=True,
            stem=True,
            language="english"
        )
        
        self.bm25_parameters = json.load(open("bm25_prefitted_on_chunks_sep2024.json", "r"))
        self.bm25_token_df_map = { token: df for token, df in zip(self.bm25_parameters['doc_freq']['indices'], self.bm25_parameters['doc_freq']['values']) }

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

        try:
            if is_str: 
                response = self.openai_client.embeddings.create(input = [text], model=model)
                self.total_costs += response.usage.prompt_tokens * self.api_costs[response.model]["input"]            
                return np.array(response.data[0].embedding)
            else:
                response = self.openai_client.embeddings.create(input = text, model=model)
                self.total_costs += response.usage.prompt_tokens * self.api_costs[response.model]["input"]
                return np.array([ _.embedding for _ in response.data ])
        except RateLimitError as e:
            logger.error(f"Rate limit error: {e}")
            raise e

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

    def embed_sparse_prefitted_bm25(self, text:str, is_query:bool=False) -> tuple[coo_array, dict[str, float]]:
        avgdl = self.bm25_parameters['avgdl']
        n_docs = self.bm25_parameters['n_docs']

        # Copied from pinecone_text.sparse.BM25Encoder
        b: float = 0.75
        k1: float = 1.2

        def _hash_text(token:str) -> int:
            return mmh3.hash(token, signed=False)

        def _find_2grams_3grams(tokens_stopwords, tokens_nostopwords):
            # For the example, assume that:
            # tokens_stopwords   : ['whi', '3d', 'computer-vis', 'is', 'cool']
            # tokens_nostopwords : ['3d', 'computer-vis', 'cool']

            A, B = tokens_stopwords, tokens_nostopwords 

            # Find all 2-grams -> [("why", "3d"), ("3d", "computer-vision"), ("computer-vision", "is"), ("is", "cool")]
            word_pairs_ngrams2 = list(zip(A, A[1:]))
            # Find all 3-grams -> [("why", "3d", "computer-vision"), ("3d", "computer-vision", "is"), ("computer-vision", "is", "cool")]
            word_pairs_ngrams3 = list(zip(A, A[1:], A[2:]))

            # Find all 2-grams -> [("3d", "computer-vision"), ("computer-vision", "cool")]
            token_pairs_ngrams2 = list(zip(B, B[1:]))
            # Find all 3-grams -> [("3d", "computer-vision", "cool")]
            token_pairs_ngrams3 = list(zip(B, B[1:], B[2:]))

            # Check which word n-grams occur within the token n-grams, which in this case is only ("3d", "computer-vision")
            ngrams2, ngrams3 = [], []
            for (w1, w2) in word_pairs_ngrams2:
                for (t1, t2) in token_pairs_ngrams2:
                    if w1.startswith(t1) and w2.startswith(t2):
                        # Store ngram as "3dcomputer-vision", so that it's a single word which can be hashed into an integer and stored
                        # in the sparse vector. Break so the word ngram is only added once, even if the token ngram occurs multiple times.
                        ngrams2.append((t1 + t2, (t1, t2)))
                        break
            
            for (w1, w2, w3) in word_pairs_ngrams3:
                for (t1, t2, t3) in token_pairs_ngrams3:
                    if w1.startswith(t1) and w2.startswith(t2) and w3.startswith(t3):
                        # Store ngram as a single word which can be hashed into an integer and stored
                        # in the sparse vector. Break so the word ngram is only added once, even if the token ngram occurs multiple times.
                        ngrams3.append((t1 + t2 + t3, (t1, t2, t3)))
                        break
            
            return ngrams2, ngrams3

        tokens_stopwords = self.bm25_tokenizer_stopwords(text)
        tokens_nostopwords = self.bm25_tokenizer_nostopwords(text)
        ngrams2, ngrams3 = _find_2grams_3grams(tokens_stopwords, tokens_nostopwords)

        # if is_query:
        #     print("tokens_stopwords:", tokens_stopwords)
        #     print("tokens_nostopwords:", tokens_nostopwords)

        #     print("ngrams2:", ngrams2)
        #     print("ngrams3:", ngrams3)

        tokens = tokens_nostopwords + [ _[0] for _ in ngrams2 ] + [_[0] for _ in ngrams3 ]

        ### Why is there a difference between encoding a document and encoding a query? # TODO explain
        
        if(is_query):
            # Encode query
            
            def _get_df(token:str) -> float:
                return self.bm25_token_df_map.get(_hash_text(token), 1)

            # All 1grams (so words), 2grams, 3grams
            N1, N2, N3 = tokens_nostopwords, ngrams2, ngrams3

            # dfs = Document Frequencies
            tokens, indices, dfs = [], [], []

            for token in set(N1):
                tokens.append(token)
                indices.append(_hash_text(token))
                dfs.append( _get_df(token) )
            for token, (t1, t2) in set(N2):
                tokens.append(token)
                indices.append(_hash_text(token))
                df_harmonic_mean = .5 / ( 1/_get_df(t1) + 1/_get_df(t2))
                # Use actual 2gram document frequency if available (unlikely), and harmonic mean otherwise 
                dfs.append( max(_get_df(token), df_harmonic_mean) )
            for token, (t1, t2, t3) in set(N3):
                tokens.append(token)
                indices.append(_hash_text(token))
                # Use actual 3gram document frequency if available (unlikely), and harmonic mean otherwise
                df_harmonic_mean = .25 / ( 1/_get_df(t1) + 1/_get_df(t2) + 1/_get_df(t3))
                dfs.append( max(_get_df(token), df_harmonic_mean) )

            # Calculate the normalized IDF (inverse document frequency)
            dfs = np.array(dfs).astype(int)             # Document Frequencies
            idfs = np.log((n_docs + 1) / (dfs + 0.5))   # Inverse Document Frequencies
            idfs_norm = idfs / idfs.sum()               # Normalized Inverse Document Frequencies

            for token, idx, df, _idf in zip(tokens, indices, dfs, idfs_norm):
                logger.info(f"word={token:>20} token={idx:>10} df={df:>6} idf= {_idf:.4f}")
            
            # Create the sparse array from the idf values
            array = coo_array(( idfs_norm, (np.zeros(len(idfs_norm),dtype=int), indices) ))

            # Get all N1 tokens (so just the words from the query) and map to their idf value
            keywords_idf_map = { token:idf for token, idf in zip(tokens, idfs) if token in N1 }
            keywords_idf_sum = sum(keywords_idf_map.values())
            # Now normalize the map
            for token, idf in keywords_idf_map.items(): keywords_idf_map[token] = idf / keywords_idf_sum
            
            return array, keywords_idf_map
        
        else:
            # Encode document
            tokens = tokens_nostopwords + [ _[0] for _ in ngrams2 ] + [_[0] for _ in ngrams3 ]
            # Count how often a token occurs within the text
            hash_counts = Counter((_hash_text(token) for token in tokens))
            indices, token_frequencies = list(hash_counts.keys()), list(hash_counts.values())
            
            # Normalize token frequencies
            token_frequencies = np.array(token_frequencies)
            token_frequencies_normed = token_frequencies / (
                k1 * (1.0 - b + b * (sum(token_frequencies) / avgdl)) + token_frequencies
            )

            # Create the sparse array from the document frequencies
            array = coo_array(( token_frequencies_normed, (np.zeros(len(token_frequencies_normed),dtype=int), indices) ))
            return array, {}

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

if __name__ == "__main__":
    print(instance)
    result = instance.embed_sparse_prefitted_bm25("Why 3D Computer-vision is cool:", is_query=True)
    print("\n----")
    print(result)