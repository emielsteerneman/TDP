# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from abc import ABC, abstractmethod
# Local libraries
from data_structures.Sentence import Sentence
from data_structures.Paragraph import Paragraph

class ClientInterface(ABC):
    """Abstract class that holds the data access interface for the client"""

    # @abstractmethod
    # def reset_everything(self) -> None:
    #     """Resets the client"""
    #     raise NotImplementedError
        