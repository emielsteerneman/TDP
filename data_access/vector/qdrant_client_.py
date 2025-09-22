# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import dotenv
import time
# Third party libraries
import numpy as np
from scipy.sparse import coo_array
from qdrant_client import QdrantClient as Qdrant
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType, PointStruct
# Local libraries
from data_access.vector.client_interface import ClientInterface
from data_access.vector.vector_filter import VectorFilter
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from MyLogger import logger
from uniqid import uniqid

def paragraph_chunk_to_payload(chunk: ParagraphChunk):
    return {
        "league_major": chunk.tdp_name.league.league_major,
        "league_minor": chunk.tdp_name.league.league_minor,
        "league_sub": chunk.tdp_name.league.league_sub,
        "team": chunk.tdp_name.team_name.name,
        "year": chunk.tdp_name.year,
        "title": chunk.title,
        "text": chunk.text
    }

class QdrantClient(ClientInterface):

    INDEX_NAME_PARAGRAPH = "paragraph"

    VECTOR_SIZE = 384

    def __init__(self):
        logger.info("Initializing Qdrant client")
        self.client = Qdrant(host="localhost", port=6333)
        self._ensure_paragraph_collection(self.VECTOR_SIZE)

    def store_paragraph_chunk(self, chunk: ParagraphChunk, dense_vector:np.ndarray, sparse_vector:coo_array) -> None:
        self.client.upsert(
            collection_name=self.INDEX_NAME_PARAGRAPH,
            points=[
                PointStruct(
                    vector = {"dense": dense_vector},
                    payload = paragraph_chunk_to_payload(chunk)
                )
            ])
        logger.info(f"Upserted '{chunk.title}'")

    def query_paragraph_chunks(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=10, filter:VectorFilter=None, include_metadata=True) -> list[Paragraph]:
        pass

    def _ensure_paragraph_collection(self, vector_size:int):
        name = self.INDEX_NAME_PARAGRAPH
        
        field_schema = {
            "league_major": PayloadSchemaType.KEYWORD,
            "league_minor": PayloadSchemaType.KEYWORD,
            "league_sub": PayloadSchemaType.KEYWORD,
            "team": PayloadSchemaType.KEYWORD,
            "year": PayloadSchemaType.INTEGER,
        }
        
        if self.client.collection_exists(collection_name=name):
            logger.debug(f"Collection '{name}' exists")
            indices = set(self.client.get_collection(name).payload_schema.keys())
            if set(field_schema.keys()) == indices:
                logger.debug(f"Collection '{name}' has correct indices")
                return
        
        logger.info(f"Creating collection '{name}'")
        
        self.client.delete_collection(collection_name=name)
        self.client.create_collection(
            collection_name=name,
            vectors_config={
                "dense": VectorParams(
                    size=vector_size, 
                    distance=Distance.COSINE
                )
            }
        )

        for field, schema in field_schema.items():
            logger.debug(f"Creating index '{field}'")
            self.client.create_payload_index(collection_name=name, field_name=field, field_schema=schema)

        logger.info(f"Collection '{name}' created")