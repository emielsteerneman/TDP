# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Third party libraries
import dotenv
dotenv.load_dotenv()
import numpy as np
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, MilvusClient
# Local libraries
from data_access.vector.client_interface import ClientInterface
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.Sentence import Sentence
from MyLogger import logger


class MyMilvusClient(ClientInterface):
    
    COLLECTION_NAME_PARAGRAPH = "paragraph"
    COLLECTION_NAME_QUESTION = "question"

    def __init__(self, client:MilvusClient) -> None:
        logger.info("Initializing Milvus client")
        self.client = client

    def create_collection_paragraph(self):
        # https://milvus.io/docs/manage-collections.md

        fields = [
            # Why do I need to specify the primary key field? Is there no default primary key field?
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),

            FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=384),
            FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),

            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000, is_primary=False),
            FieldSchema(name="start", dtype=DataType.INT64, is_primary=False),
            FieldSchema(name="end", dtype=DataType.INT64, is_primary=False),
            FieldSchema(name="paragraph_sequence_id", dtype=DataType.INT64, is_primary=False),
            FieldSchema(name="chunk_sequence_id", dtype=DataType.INT64, is_primary=False),

            FieldSchema(name="tdp_name", dtype=DataType.VARCHAR, max_length=5000, is_primary=False),
            FieldSchema(name="league", dtype=DataType.VARCHAR, max_length=5000, is_primary=False),
            FieldSchema(name="team", dtype=DataType.VARCHAR, max_length=5000, is_primary=False),
            FieldSchema(name="year", dtype=DataType.INT64, is_primary=False)
        ]

        collection_schema = CollectionSchema(fields=fields, description="Paragraph chunks", enable_dynamic_fields=False)

        # Which fields are indexed automatically? Do I need to manually create an index for my VARCHAR fields as well?
        index_params = self.client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", index_type="FLAT", index_name="dense_vector")
        index_params.add_index(field_name="sparse_vector", index_type="FLAT", index_name="sparse_vector")
        index_params.add_index(field_name="tdp_name", index_name="tdp_name")
        index_params.add_index(field_name="league", index_name="league")
        index_params.add_index(field_name="team", index_name="team")
        index_params.add_index(field_name="year", index_name="year")

        self.client.create_collection(
            collection_name=self.COLLECTION_NAME_PARAGRAPH,
            collection=collection_schema,
            dimension=384, # Why do I need this? I already have a FLOAT_VECTOR field schema with dim=384
            index_params=index_params,
            auto_id=True # Why do I need this? I already have a field schema with auto_id=True
        )    
    
    def test(self):
        indexes = self.client.list_indexes(collection_name=self.COLLECTION_NAME_PARAGRAPH)
        print(indexes)

    @staticmethod
    def default_client():
        client = MilvusClient()
        return MyMilvusClient(client)
    
if __name__ == "__main__":
    client = MyMilvusClient.default_client()
    client.create_collection_paragraph()
    client.test()
    logger.info("Collection created")
    logger.info("Done")
