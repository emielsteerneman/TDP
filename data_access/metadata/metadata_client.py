# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from abc import ABC, abstractmethod
# Third party libraries
import pymongo
import pymongo.collection
import pymongo.database
from pymongo.mongo_client import MongoClient
# Local libraries
from data_structures.TDP import TDP
from data_structures.TDPName import TDPName
from data_structures.Paragraph import Paragraph   
from MyLogger import logger

class MetadataTDPClient(ABC):
    @abstractmethod
    def insert_tdp(self, tdp:TDP):
        raise NotImplementedError

    @abstractmethod
    def find_tdps(self, 
            team:str|list[str]=None, 
            year:int|list[int]=None, year_min:int=None, year_max:int=None,
            league:str|list[str]=None,
            filehash:str=None,
            offset:int=0, limit:int=0
        ) -> list[TDP]:
        raise NotImplementedError

    @abstractmethod
    def drop_tdps(self):
        raise NotImplementedError

    @abstractmethod
    def ensure_collection_tdp(self):
        raise NotImplementedError

class MetadataParagraphClient(ABC):
    @abstractmethod
    def insert_paragraph(self, paragraph:Paragraph):
        raise NotImplementedError

    # @abstractmethod
    # def find_paragraphs(self, 
    #         team:str|list[str]=None, 
    #         year:int|list[int]=None, year_min:int=None, year_max:int=None,
    #         league:str|list[str]=None,
    #         filehash:str=None,
    #         offset:int=0, limit:int=0
    #     ) -> list[Paragraph]:
    #     raise NotImplementedError

    @abstractmethod
    def drop_paragraphs(self):
        raise NotImplementedError

    @abstractmethod
    def ensure_collection_paragraph(self):
        raise NotImplementedError

class MongoDBClient(MetadataTDPClient, MetadataParagraphClient):
    
    def __init__(self, connection_string:str):
        self.client = MongoClient(connection_string, serverSelectionTimeoutMS = 3000)
        MongoClient()
        self.ensure_collection_tdp()
        self.ensure_collection_paragraph()

    """ MetadataTDPClient implementation"""

    def count_tdps(self) -> int:
        db:pymongo.database.Database = self.client.get_database("metadata")
        col:pymongo.collection.Collection = db.get_collection("tdp")
        n_tdps = col.count_documents({})
        print(f"Number of TDPs: {n_tdps}")
        return n_tdps
    
    def insert_tdp(self, tdp:TDP):
        tdp_dict = {
            "team": tdp.tdp_name.team_name.name,
            "year": tdp.tdp_name.year,
            "league": tdp.tdp_name.league.name,
            "index": tdp.tdp_name.index,
            "filename": tdp.tdp_name.filename,
            "filehash": tdp.filehash
        }

        logger.info(f"Inserting TDP {tdp.tdp_name}")
        
        db:pymongo.database.Database = self.client.get_database("metadata")
        col:pymongo.collection.Collection = db.get_collection("tdp")

        # Ensure uniqueness
        document = col.find_one({ "team" : tdp_dict["team"], "year" : tdp_dict["year"], "league" : tdp_dict["league"], "index" : tdp_dict["index"] })
        if document is not None:
            raise ValueError(f"TDP {tdp.tdp_name} already exists in the database")

        idx = col.insert_one(tdp_dict)
        logger.info(f"Inserted TDP {tdp.tdp_name} with id {idx.inserted_id}")

    def find_tdps(self, 
            team:str|list[str]=None, 
            year:int|list[int]=None, year_min:int=None, year_max:int=None,
            league:str|list[str]=None,
            filehash:str=None,
            offset:int=0, limit:int=0
        ) -> list[TDP]:
        
        db:pymongo.database.Database = self.client.get_database("metadata")
        col:pymongo.collection.Collection = db.get_collection("tdp")
        
        filters = {}
        # Team filter
        if team is not None:
            if isinstance(team, str): filters["team"] = { "$in": [team] }
            else:                     filters["team"] = { "$in": team }
        # Year filter
        if year_min or year_max: filters["year"] = {}
        if year_min is not None: filters["year"]["$gte"] = year_min
        if year_max is not None: filters["year"]["$lte"] = year_max
        if year     is not None:
            if isinstance(year, int): filters["year"] = { "$in": [year] }
            else:                     filters["year"] = { "$in": year }
        # League filter
        if league is not None: 
            if isinstance(league, str): filters["league"] = { "$in": [league] }
            else:                       filters["league"] = { "$in": league }
        # Filehash filter
        if filehash is not None: filters["filehash"] = filehash

        # TODO replace skip and limit with $facet ( https://codebeyondlimits.com/articles/pagination-in-mongodb-the-only-right-way-to-implement-it-and-avoid-common-mistakes )
        tdp_cursor = col.find(filters).skip(offset).limit(limit)

        return [ 
            TDP(TDPName.from_string(tdp["filename"]).set_filehash(tdp["filehash"])) 
            for tdp in tdp_cursor ]

    def drop_tdps(self):
        db:pymongo.database.Database = self.client.get_database("metadata")
        col:pymongo.collection.Collection = db.get_collection("tdp")
        col.drop()

    def ensure_collection_tdp(self):
        # self.client.drop_database("metadata")
        # Ensure that database "metadata" exists
        if "metadata" not in self.client.list_database_names():
            logger.info("Creating database 'metadata'")
        db = self.client.get_database("metadata")

        # Ensure that the collection "tdp" exists
        if "tdp" not in db.list_collection_names():
            logger.info("Creating collection 'tdp'")
        col = db.get_collection("tdp")

        # Ensure that compound index on team, year, league, index exists
        if "team_1_year_1_league_1_index_1" not in col.index_information():
            logger.info("Creating index on [team, year, league, index]")
        col.create_index([
            ("team", pymongo.ASCENDING), 
            ("year", pymongo.ASCENDING), 
            ("league", pymongo.ASCENDING),
            ("index", pymongo.ASCENDING)
            # Unfortunately, the index cannot be unique becaue Azure CosmosDB does not support it for whatever stupid reason
        ])

    """ MetadataParagraphClient implementation"""

    def insert_paragraph(self, paragraph:Paragraph):
        
        if paragraph.tdp_name is None:
            raise ValueError(f"TDPName is None for paragraph {paragraph.text_raw}")
        
        paragraph_dict = {
            "team": tdp.tdp_name.team_name.name,
            "year": tdp.tdp_name.year,
            "league": tdp.tdp_name.league.name,
            "index": tdp.tdp_name.index,
            "filename": paragraph.tdp_name.filename,
            "sequence_id": paragraph.sequence_id,
            "title": paragraph.text_raw,
            "text": paragraph.content_raw(),
        }

        db:pymongo.database.Database = self.client.get_database("metadata")
        col:pymongo.collection.Collection = db.get_collection("paragraph")

        idx = col.insert_one(paragraph_dict)
        logger.info(f"Inserted paragraph '{paragraph.text_raw}' with id {idx.inserted_id}")

    def ensure_collection_paragraph(self):
        # self.client.drop_database("metadata")
        # Ensure that database "metadata" exists
        if "metadata" not in self.client.list_database_names():
            logger.info("Creating database 'metadata'")
        db = self.client.get_database("metadata")

        # Ensure that the collection "paragraph" exists
        if "paragraph" not in db.list_collection_names():
            logger.info("Creating collection 'paragraph'")
        col = db.get_collection("paragraph")

        # Ensure that compound index on team, year, league, index exists
        if "team_1_year_1_league_1_index_1" not in col.index_information():
            logger.info("Creating index on [team, year, league, index]")
        col.create_index([
            ("team", pymongo.ASCENDING), 
            ("year", pymongo.ASCENDING), 
            ("league", pymongo.ASCENDING),
            ("index", pymongo.ASCENDING)
            # Unfortunately, the index cannot be unique becaue Azure CosmosDB does not support it for whatever stupid reason
        ])

    def drop_paragraphs(self):
        db:pymongo.database.Database = self.client.get_database("metadata")
        col:pymongo.collection.Collection = db.get_collection("paragraph")
        col.drop()

    def test_performance(self):

        import time
        import random

        db:pymongo.database.Database = self.client.get_database("tdps")
                
        # Just delete the collection
        db.drop_collection("test")

        col:pymongo.collection.Collection = db.get_collection("test")
        # col.create_index("team")
        
        # Create compound index on team, year, city
        col.create_index([("team", pymongo.ASCENDING), ("year", pymongo.ASCENDING), ("city", pymongo.ASCENDING)])

        teams = [ f"team{i}" for i in range(1, 10000)]
        years = [ f"year{i}" for i in range(1, 10000)]
        cities = [ f"city{i}" for i in range(1, 10000)]
        
        for _ in range(100):
            print(f"\r {_}    ", end="")
            bulk = []
            for i in range(10000):
                bulk.append({
                    "team": random.choice(teams),
                    "year": random.choice(years),
                    "city": random.choice(cities)
                })    
            col.insert_many(bulk)

        print(f"\rDocuments: {col.count_documents({})}")

        # =================

        N = 1000

        start = time.time()
        for i in range(N):
            if i % 100 == 0: print(f"\r {i}    ", end="")
            random_team = random.choice(teams)
            random_year = random.choice(years)
            random_city = random.choice(cities)

            idx = col.find(
                {"team": random_team}, 
                {}
            )
            len(list(idx))

        duration = time.time() - start
        print(f"Elapsed time: {time.time() - start}")
        print(f"Milliseconds per query: {1000*duration/N}")

        start = time.time()
        for i in range(N):
            if i % 100 == 0: print(f"\r {i}    ", end="")
            random_team = random.choice(teams)
            random_year = random.choice(years)
            random_city = random.choice(cities)

            idx = col.find({
                "team": random_team,
                "year": random_year,
                "city": random_city
            }, {})
            len(list(idx))
            
        duration = time.time() - start
        print(f"Elapsed time: {duration}")
        print(f"Milliseconds per query: {1000*duration/N}")

if __name__ == "__main__":
    
    from custom_dotenv import load_dotenv
    load_dotenv()

    print(os.getenv("MONGODB_CONNECTION_STRING"))
    client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
    client.count_tdps()

    tdps = client.find_tdps(limit=10, offset=1)
    print(f"Found {len(tdps)} TDPs")
    for tdp in tdps: print(tdp.tdp_name.team_name, tdp.tdp_name.year)

    leagues = client.list_leagues()
    print(f"Found {len(leagues)} leagues")
    for league in leagues: print("  -", league)