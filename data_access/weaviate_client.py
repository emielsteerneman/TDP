# Third party libraries
import numpy as np
import pickle
import weaviate
import weaviate.classes as wvc
import weaviate.classes.config as wvcc

# Local libraries
from data_structures.Sentence import Sentence
from extraction import extractor as E
import utilities as U
from MyLogger import logger

from data_access.client_interface import ClientInterface

class WeaviateClient(ClientInterface):

    collection_name_sentences = "Sentences"

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
            vector=vector.tolist()
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

    def reset_everything(self) -> None:
        self.create_weaviate_schema(self.client, overwrite=True, headless=True)

    def create_weaviate_schema(self, overwrite: bool=False, headless: bool=False) -> wvc.Collection:
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



# collection = client.collections.get("Sentence")
# count = collection.aggregate.over_all(total_count=True).total_count
# logger.info(f"Collection 'Sentence' has {count} objects")


# collection = create_weaviate_schema(client, overwrite=True)

# logger.info("Loading TDPs from pickle file..")
# file = open("tdps.pkl", "rb")
# tdps = pickle.load(file)
# logger.info(f"Loaded {len(tdps)} TDPs from pickle file")
# tdps = [tdp for tdp in tdps if tdp is not None]

# for i_tdp, tdp in enumerate(tdps):
#     logger.info(f"Processing TDP {i_tdp+1}/{len(tdps)}")

#     embedder = Embeddings.instance

#     sentences = [ sentence for paragraph in tdp.paragraphs for sentence in paragraph.sentences ]
#     for sentence in sentences:
#         vector = embedder.embed(sentence.text_raw)

#         uuid = collection.data.insert(
#             properties={
#                 "team": tdp.team,
#                 "year": tdp.year,
#                 "league": tdp.league,
#                 "text": sentence.text_raw
#             },
#             vector=vector.tolist()
#         )
#         # print(f"# {uuid} {sentence.text_raw}\n")

# # Search
# query = "What path planning techniques exist?"
# vector = embedder.embed(query)
# results = collection.query.near_vector(
#     vector.tolist(), limit=5
#     # filters=wvc.query.Filter.by_property("team").equal("SomeTeam")
# )

# print("\n\n")
# # print(f"Results: {results}")

# for r in results.objects:
#     print("\n\n")
#     print(r.properties["text"])


# client.close()