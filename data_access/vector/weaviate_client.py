# Third party libraries
import numpy as np
import pickle
import weaviate
import weaviate.client
import weaviate.classes as wvc
import weaviate.classes.config as wvcc
# Local libraries
from data_structures.Sentence import Sentence
from data_structures.Paragraph import Paragraph
from data_structures.TDPName import TDPName
from MyLogger import logger

from data_access.vector.client_interface import ClientInterface

class WeaviateClient(ClientInterface):

    collection_name_sentences = "Sentence"
    collection_name_paragraphs = "Paragraph"

    def __init__(self, client: weaviate.client.Client) -> None:
        self.client = client

    def store_sentence(self, sentence: Sentence) -> None:
        """Stores a sentence in the collection"""
        if sentence.embedding is None:
            raise ValueError("The sentence does not have an embedding")

        collection = self.client.collections.get(self.collection_name_sentences)
        collection.data.insert(
            properties={
                "team": sentence.team,
                "year": sentence.year,
                "league": sentence.league,
                "text": sentence.text_raw
            },
            vector = sentence.embedding.tolist()
        )

    def search_sentences_by_embedding(self, vector:np.array, team: str=None, year: int=None, league: str=None, limit:int=0) -> list[Sentence]:
        """Loads sentences from the collection"""
        
        filters = []
        if team is not None:
            filters.append(wvc.query.Filter.by_property("team").equal(team))
        if year is not None:
            filters.append(wvc.query.Filter.by_property("year").equal(year))
        if league is not None:
            filters.append(wvc.query.Filter.by_property("league").equal(league))

        collection = self.client.collections.get("Sentence")

        results = collection.query.near_vector(vector.tolist(), limit=limit, filters=filters)

        sentences = []
        for r in results.objects:
            sentences.append(Sentence(
                team=r.properties["team"],
                year=r.properties["year"],
                league=r.properties["league"],
                text_raw=r.properties["text"]
            ))

        return sentences

    def store_paragraph(self, paragraph: Paragraph, embedding:np.ndarray) -> None:
        """Stores a paragraph in the collection"""
        if embedding is None:
            raise ValueError("The paragraph does not have an embedding")

        collection = self.client.collections.get(self.collection_name_paragraphs)
        collection.data.insert(
            properties={
                "team": paragraph.tdp_name.team_name.name,
                "year": paragraph.tdp_name.year,
                "league": paragraph.tdp_name.league.name,
                "index": paragraph.tdp_name.index,
                "title": paragraph.text_raw,
                "text": paragraph.content_raw()
            },
            vector = embedding.tolist()
        )

    def search_paragraphs_by_embedding(self, vector:np.array, team: str=None, year: int=None, league: str=None, limit:int=0) -> list[Paragraph]:
        """Loads paragraphs from the collection"""
        
        for item in self.client.collections.get(self.collection_name_paragraphs).iterator():
            print(item.uuid, item.properties.keys())

        # filters = []
        # if team is not None:
        #     filters.append(wvc.query.Filter.by_property("team").equal(team))
        # if year is not None:
        #     filters.append(wvc.query.Filter.by_property("year").equal(year))
        # if league is not None:
        #     filters.append(wvc.query.Filter.by_property("league").equal(league))

        collection = self.client.collections.get(self.collection_name_paragraphs)

        results = collection.query.near_vector(vector.tolist(), limit=limit)
        print(results)

        # for r in results.objects:
        #     print(r.properties["team"], r.properties["year"], r.properties["league"], r.properties["index"], r.properties["title"])

    def reset_everything(self) -> None:
        # self.create_weaviate_schema_sentences(self.client, overwrite=True, headless=True)
        self.create_weaviate_schema_paragraphs(overwrite=True, headless=True)

    def create_weaviate_schema_sentences(self, overwrite:bool=False, headless:bool=False):
        cn = self.collection_name_sentences
        
        if not overwrite and self.client.collections.exists(cn):
            return self.client.collections.get(cn)
        
        if not headless:
            answer = input(f"You are about to delete the current schema '{cn}' and create a new one. Are you sure? (y/n)")
            if answer.lower() != "y":
                return self.client.collections.get(cn)

        # Delete the schema if it exists
        self.client.collections.delete(cn)
        logger.info(f"Deleted the schema '{cn}'")

        # Create the schema
        # https://weaviate.io/developers/weaviate/manage-data/collections
        collection = self.client.collections.create(
            name=cn,
            description="A sentence",
            vector_index_config=wvc.config.Configure.VectorIndex.flat(
                distance_metric=wvc.config.VectorDistances.COSINE,
            ),
            properties=[
                wvcc.Property(name="team", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="year", data_type=wvcc.DataType.INT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="league", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="index", data_type=wvcc.DataType.INT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="text", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=True),
            ]
        )
        logger.info(f"Created the schema '{cn}'")

        return collection

    def create_weaviate_schema_paragraphs(self, overwrite:bool=False, headless:bool=False):
        cn = self.collection_name_paragraphs
        
        if not overwrite and self.client.collections.exists(cn):
            return self.client.collections.get(cn)
        
        if not headless:
            answer = input(f"You are about to delete the current schema '{cn}' and create a new one. Are you sure? (y/n)")
            if answer.lower() != "y":
                return self.client.collections.get(cn)

        # Delete the schema if it exists
        self.client.collections.delete(cn)
        logger.info(f"Deleted the schema '{cn}'")

        # Create the schema
        # https://weaviate.io/developers/weaviate/manage-data/collections
        collection = self.client.collections.create(
            name=cn,
            description="A paragraph",
            vector_index_config=wvc.config.Configure.VectorIndex.flat(
                distance_metric=wvc.config.VectorDistances.COSINE,
            ),
            properties=[
                wvcc.Property(name="team", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="year", data_type=wvcc.DataType.INT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="league", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="index", data_type=wvcc.DataType.INT, index_filterable=True, index_searchable=False),
                wvcc.Property(name="text", data_type=wvcc.DataType.TEXT, index_filterable=True, index_searchable=True),
            ]
        )
        logger.info(f"Created the schema '{cn}'")

        return collection

    def print_statistics(self) -> None:
        collection = self.client.collections.get("Sentence")
        count = collection.aggregate.over_all(total_count=True).total_count
        logger.info(f"Collection 'Sentence' has {count} objects")

    @staticmethod
    def default_client() -> "WeaviateClient":
        client = weaviate.connect_to_custom(
            http_host="localhost",
            http_port=8081,
            http_secure=False,
            grpc_host="localhost",
            grpc_port=50051,
            grpc_secure=False,
        )
        return WeaviateClient(client)
