# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from abc import ABC, abstractmethod

class MetadataClient(ABC):
    @abstractmethod
    def list_tdps(self):
        raise NotImplementedError
    
class CosmosDBClient(MetadataClient):
    
    def __init__(self):
        pass      
    
    def list_tdps(self):
        return super().list_tdps()
    