# System libraries
import os
import sys

import numpy as np

from data_access.vector.vector_filter import VectorFilter
from data_structures.ParagraphChunk import ParagraphChunk
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from abc import ABC, abstractmethod
# Local libraries
from data_structures.Sentence import Sentence
from data_structures.Paragraph import Paragraph
from scipy.sparse import coo_array

class ClientInterface(ABC):
    """Abstract class that holds the data access interface for the client"""

    @abstractmethod
    def store_paragraph_chunk(self, chunk: ParagraphChunk, dense_vector:np.ndarray, sparse_vector:coo_array) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def query_paragraph_chunks(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=10, filter:VectorFilter=None, include_metadata=True) -> list[Paragraph]:
        raise NotImplementedError