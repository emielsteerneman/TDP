# System libraries
import os
import sys

import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import dotenv
from abc import ABC, abstractmethod
# Third party libraries
# Local libraries
from MyLogger import logger

class ClientInterface(ABC):
    """Abstract class that holds the data access interface for the client"""

    @abstractmethod
    def create_text_embedding(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def create_query_embedding(self) -> None:
        raise NotImplementedError

from fastembed import TextEmbedding

class FastembedClient(ClientInterface):
    MODEL_NAME = "BAAI/bge-base-en-v1.5"

    def __init__(self):
        for m in TextEmbedding.list_supported_models():
            print(m["model"].rjust(70), "  ", m["sources"]["hf"])
            # for k, v in m["sources"].items():
            #     print(f"  {k} : {v}")

        self.model = TextEmbedding(model_name=self.MODEL_NAME, cache_dir="/home/emiel/Desktop/projects/fastembed_cache")
        logger.info(f"The model {self.model.model_name} is ready to use.")
        logger.info(self.model.get_embedding_size(self.model.model_name))

        # for m in TextEmbedding.list_supported_models():
        #     print(m['model'].rjust(80), m['dim'])

    def create_text_embedding(self, text:str) -> np.ndarray:
        return list(self.model.embed([text]))[0]
    
    def create_query_embedding(self, text:str):
        raise NotImplementedError


if __name__ == "__main__":
    c = FastembedClient()
    print(c)

    e = c.create_text_embedding("This is built to be faster and lighter than other embedding libraries e.g. Transformers, Sentence-Transformers, etc.")
