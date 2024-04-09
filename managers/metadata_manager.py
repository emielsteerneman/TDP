# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from abc import ABC, abstractmethod

class MetadataManager(ABC):
    @abstractmethod 
    def list_tdps(self):
        raise NotImplementedError