# System libraries
import os
import sys
sys.path.append(os.path.dirname(__file__))
# Third party libraries

# Local libraries
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import FileClient


""" Everything in one file until I figure out how I want to structure everything """
class ApiManager:
    def __init__(self, file_client:FileClient, metadata_client:MongoDBClient):
        self.file_client = file_client
        self.metadata_client = metadata_client
    
    def enumerate_tdps(self):
        return self.metadata_client.find_tdps()