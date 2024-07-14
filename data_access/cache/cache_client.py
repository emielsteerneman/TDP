# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from abc import ABC, abstractmethod
import time
# Third party libraries
import pymongo
import pymongo.collection
import pymongo.database
from pymongo.mongo_client import MongoClient
# Local libraries
from data_structures.TDP import TDP
from data_structures.TDPName import TDPName
from data_structures.Paragraph import Paragraph   
from data_structures.ProcessStateEnum import ProcessStateEnum
from MyLogger import logger

class CacheClient(ABC):
    @abstractmethod
    def insert_query(self, key:str, value:str, overwrite=False):
        raise NotImplementedError

    @abstractmethod
    def find_query(self, key:str) -> tuple[str, int]:
        raise NotImplementedError

    @abstractmethod
    def insert_llm(self):
        raise NotImplementedError

    @abstractmethod
    def find_llm(self):
        raise NotImplementedError

class MongoDBClient(CacheClient):
    
    def __init__(self, connection_string:str):
        self.client = MongoClient(connection_string, serverSelectionTimeoutMS = 3000)
        self.ensure_collection_cache_query()
        self.ensure_collection_cache_llm()

    def count_queries(self) -> int:
        db:pymongo.database.Database = self.client.get_database("cache")
        col:pymongo.collection.Collection = db.get_collection("query")
        n_queries = col.count_documents({})
        return n_queries

    def count_llms(self) -> int:
        db:pymongo.database.Database = self.client.get_database("cache")
        col:pymongo.collection.Collection = db.get_collection("llm")
        n_llms = col.count_documents({})
        return n_llms

    def insert_query(self, key:str, value:str):
        logger.info(f"Inserting query with key {key}")
        
        db:pymongo.database.Database = self.client.get_database("cache")
        col:pymongo.collection.Collection = db.get_collection("query")

        idx = col.update_one({"key": key}, { "$set": { "value": value, "timestamp": int(time.time()) } }, upsert=True)

        logger.info(f"Inserted query of length {len(value)} with key {key} with id {idx.upserted_id}")

    def insert_llm(self, key, value):
        logger.info(f"Inserting LLM with key {key}")

        db:pymongo.database.Database = self.client.get_database("cache")
        col:pymongo.collection.Collection = db.get_collection("llm")

        idx = col.update_one({"key": key}, { "$set": { "value": value, "timestamp": int(time.time()) } }, upsert=True)

        logger.info(f"Inserted LLM with key {key} with id {idx.upserted_id}")

    def find_query(self, key:str) -> tuple[str, int]:
        db:pymongo.database.Database = self.client.get_database("cache")
        col:pymongo.collection.Collection = db.get_collection("query")
        
        query = col.find_one({ "key": key })
        
        if query is None: 
            logger.info(f"Cache miss for query with key {key}")
            return None, None
        
        logger.info(f"Cache hit for query with key {key}")
        return query["value"], query["timestamp"]

    def find_llm(self, key:str) -> tuple[str, int]:
        db:pymongo.database.Database = self.client.get_database("cache")
        col:pymongo.collection.Collection = db.get_collection("llm")
        
        llm = col.find_one({ "key": key })
        
        if llm is None:
            logger.info(f"Cache miss for LLM with key {key}")
            return None, None
        
        logger.info(f"Cache hit for LLM with key {key}")
        return llm["value"], llm["timestamp"]
        
    def ensure_collection_cache_query(self):
        # Ensure that database "cache" exists
        if "cache" not in self.client.list_database_names():
            logger.info("Creating database 'cache'")
        db = self.client.get_database("cache")

        # Ensure that the collection "query" exists
        if "query" not in db.list_collection_names():
            logger.info("Creating collection 'query'")
        col = db.get_collection("query")

        # Ensure that index on key
        if "key_1" not in col.index_information():
            logger.info("Creating index on key")
        col.create_index("key")

    def ensure_collection_cache_llm(self):
        # Ensure that database "cache" exists
        if "cache" not in self.client.list_database_names():
            logger.info("Creating database 'cache'")
        db = self.client.get_database("cache")

        # Ensure that the collection "llm" exists
        if "llm" not in db.list_collection_names():
            logger.info("Creating collection 'llm'")
        col = db.get_collection("llm")

        # Ensure that index on key
        if "key_1" not in col.index_information():
            logger.info("Creating index on key")
        col.create_index("key")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print(os.getenv("MONGODB_CONNECTION_STRING"))
    client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
    
    print(client.count_queries())

    client.insert_query("test", "test_" + str(time.time()), overwrite=True)

    print("result:", client.find_query("test"))

    client.insert_query("test_" + str(time.time()), "test_" + str(time.time()))