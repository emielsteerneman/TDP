# System libraries
# Third party libraries
import numpy as np
from openai import OpenAI
import tiktoken
# Local libraries
from MyLogger import logger

class Embeddor:
    def __init__(self):
        self.model = None
        self.openai_client = None

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def embed_using_sentence_transformer(self, text:str | list[str]) -> np.array:
        if self.model is None:
            self.load_sentence_transformer()
        return self.model.encode(text)

    def embed_using_openai(self, text:str | list[str], model="text-embedding-3-small") -> np.array:
        if self.openai_client is None:
            self.load_openai_client()
        
        is_str:bool = type(text) == str

        if is_str: 
            response = self.openai_client.embeddings.create(input = [text], model=model)
            # print(response.usage.total_tokens, response.usage.prompt_tokens)
            return np.array(response.data[0].embedding)
        else:
            response = self.openai_client.embeddings.create(input = text, model=model)
            return np.array([ _.embedding for _ in response.data ])

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