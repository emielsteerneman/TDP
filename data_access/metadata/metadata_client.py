# System libraries
import os
import sys

import pymongo.collection
import pymongo.database
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from abc import ABC, abstractmethod

# Third party libraries
import pymongo
from pymongo.mongo_client import MongoClient

class MetadataClient(ABC):
    @abstractmethod
    def list_tdps(self):
        raise NotImplementedError
    
class CosmosDBClient(MetadataClient):
    
    def __init__(self, connection_string:str):
        self.client = MongoClient(connection_string)
        print(self.client)
        print(f"Databases: {self.client.list_database_names()}")

    def list_tdps(self):
        db:pymongo.database.Database = self.client.get_database("tdps")
        col:pymongo.collection.Collection = db.get_collection("tdp")
        entry = col.find_one()
        print(entry)
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    client = CosmosDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
    print()
    client.list_tdps()
