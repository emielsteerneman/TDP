# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import time
# Third party libraries
import dotenv
import numpy as np
from pinecone import Pinecone, Vector, SparseValues, UpsertResponse, QueryResponse
from scipy.sparse import coo_array
# Local libraries
from data_access.vector.client_interface import ClientInterface
from data_access.vector.vector_filter import VectorFilter
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.Sentence import Sentence
from data_structures.TDPName import TDPName
from MyLogger import logger
from uniqid import uniqid

def filter_to_dict(filter:VectorFilter=None) -> dict:
    d = {}

    if filter is None:
        return d

    if filter.team is not None: 
        d["team"] = filter.team
    elif filter.teams is not None: 
        d["team"] = { "$in": filter.teams }
    
    if filter.year is not None:
        d["year"] = filter.year
    elif filter.year_min is not None or filter.year_max is not None:
        d["year"] = {}
        if filter.year_min is not None: 
            d["year"]["$gte"] = filter.year_min
        if filter.year_max is not None: 
            d["year"]["$lte"] = filter.year_max

    if filter.league is not None: 
        d["league"] = filter.league
    elif filter.leagues is not None: 
        d["league"] = { "$in": filter.leagues }
    
    return d

class PineconeClient(ClientInterface):

    INDEX_NAME_PARAGRAPH = "paragraph"
    INDEX_NAME_QUESTION = "question"
    INDEX_NAME_DEVELOPMENT = "development"

    def __init__(self, api_key:str) -> None:
        logger.info("Initializing Pinecone client")
        self.client = Pinecone(api_key=api_key)
        self.index_paragraph = None
        self.index_question = None
        self.index_development = None

    """ Paragraph chunks """

    def get_paragraph_chunks_metadata_by_id(self, ids:list[str]) -> list[dict]:
        logger.info(f"Retrieving paragraphs by id with {len(ids)} ids")

        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        response = self.index_paragraph.fetch(ids)
        
        metadatas = [vector.metadata for vector in response['vectors'].values()]

        return metadatas

    def get_paragraph_chunks_by_tdpname(self, tdp_name:TDPName) -> list[str]:
        logger.info(f"Retrieving paragraphs by tdp name {tdp_name}")

        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        response = list(self.index_paragraph.list(prefix=tdp_name.filename))

        return [] if not len(response) else response[0]

    def store_paragraph_chunk(self, chunk: ParagraphChunk, dense_vector:np.ndarray, sparse_vector:coo_array) -> None:
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        vector_id = chunk.tdp_name.filename + "__" + str(chunk.paragraph_sequence_id) + "__" + str(chunk.sequence_id)
                
        # 40kb metadata limit
        if 40000*0.8 < len(chunk.text):
            logger.error(f"Metadata limit exceeded for paragraph {vector_id}")
            raise ValueError("Metadata limit exceeded")

        metadata = {
            'text': chunk.text,
            'start': chunk.start,
            'end': chunk.end,
            'paragraph_sequence_id': chunk.paragraph_sequence_id,
            'chunk_sequence_id': chunk.sequence_id,

            'tdp_name': chunk.tdp_name.filename,
            'paragraph_title': chunk.title,
            'league': chunk.tdp_name.league.name,
            'team': chunk.tdp_name.team_name.name,
            'year': chunk.tdp_name.year,

            'run_id': uniqid
        }
                
        sparse_vector = SparseValues(indices=sparse_vector.col.tolist(), values=sparse_vector.data.tolist())
        vector = Vector(id=vector_id, values=dense_vector.tolist(), sparse_values=sparse_vector, metadata=metadata)

        self.index_paragraph.upsert([vector])

    def query_paragraph_chunks(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=10, filter:VectorFilter=None, include_metadata=True) -> list[Paragraph]:
        logger.info(f"Querying index {self.INDEX_NAME_PARAGRAPH}")
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        t_start = time.time()
        response:QueryResponse = self.index_paragraph.query(
            vector=dense_vector.tolist(),
            sparse_vector={'indices':sparse_vector.col.tolist(), 'values':sparse_vector.data.tolist()},
            top_k=limit,
            include_metadata=include_metadata,
            filter=filter_to_dict(filter)
        )
        t_stop = time.time()

        logger.info(f"Index queried. Duration: {t_stop-t_start:.2f}s")
        return response

    def delete_paragraph_chunks(self):
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_PARAGRAPH}")
        
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        # if there actually are entries in the index
        if 0 < self.index_paragraph.describe_index_stats().total_vector_count:
            response:dict = self.index_paragraph.delete(delete_all=True)
            if len(response.keys()) > 0:
                logger.error("Errors occured while deleting paragraphs")
                for message in response:
                    logger.error(message, ":", response[message])

    def delete_paragraph_chunks_by_tdpname(self, tdp_name:TDPName) -> bool:
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_PARAGRAPH} with name {tdp_name}")
        
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        logger.info(f"Number of vectors before deletion: {self.count_paragraph_chunks()}")

        error = False

        # https://docs.pinecone.io/guides/data/manage-rag-documents
        for ids in self.index_paragraph.list(prefix=tdp_name.filename):
            response:dict = self.index_paragraph.delete(ids)

            if len(response.keys()) > 0:
                error = True
                logger.error("Errors occured while deleting paragraphs")
                for message in response:
                    logger.error(message, ":", response[message])

        logger.info(f"Number of vectors  after deletion: {self.count_paragraph_chunks()}")

        return error

    def count_paragraph_chunks(self) -> int:
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        return self.index_paragraph.describe_index_stats().total_vector_count

    """ Questions """

    def get_questions_metadata_by_id(self, ids:list[str]) -> list[dict]:
        logger.info(f"Retrieving questions by id with {len(ids)} ids")
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        response = self.index_question.fetch(ids)
        
        metadatas = [vector.metadata for vector in response['vectors'].values()]

        return metadatas

    def get_questions_by_tdpname(self, tdp_name:TDPName) -> list[str]:
        logger.info(f"Retrieving questions by tdp name {tdp_name}")
        
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        response = list(self.index_question.list(prefix=tdp_name.filename))
        
        return [] if not len(response) else response[0]

    def store_question(self, chunk: ParagraphChunk, question: str, dense_vector:np.ndarray, sparse_vector:coo_array) -> None:
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        vector_id = chunk.tdp_name.filename + "__" + str(chunk.paragraph_sequence_id) + "__" + str(chunk.sequence_id)
                
        metadata = {
            'question': question,
            'paragraph_sequence_id': chunk.paragraph_sequence_id,
            'chunk_sequence_id': chunk.sequence_id,
            
            'tdp_name': chunk.tdp_name.filename,
            'paragraph_title': chunk.title,
            'league': chunk.tdp_name.league.name,
            'team': chunk.tdp_name.team_name.name,
            'year': chunk.tdp_name.year,

            'run_id': uniqid
        }
        sparse_vector = SparseValues(indices=sparse_vector.col.tolist(), values=sparse_vector.data.tolist())
        vector = Vector(id=vector_id, values=dense_vector.tolist(), sparse_values=sparse_vector, metadata=metadata)

        self.index_question.upsert([vector])

    def query_questions(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=10, filter:VectorFilter=None, include_metadata=True) -> list[ParagraphChunk]:
        logger.info(f"Querying index {self.INDEX_NAME_QUESTION}")
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        t_start = time.time()
        response:QueryResponse = self.index_question.query(
            vector=dense_vector.tolist(),
            sparse_vector={'indices':sparse_vector.col.tolist(), 'values':sparse_vector.data.tolist()},
            top_k=limit,
            include_metadata=include_metadata,
            filter=filter_to_dict(filter)
        )
        t_stop = time.time()

        logger.info(f"Index queried. Duration: {t_stop-t_start:.2f}s")
        return response

    def delete_questions(self):
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_QUESTION}")

        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)

        # if there actually are entries in the index
        if 0 < self.index_question.describe_index_stats().total_vector_count:
            response:dict = self.index_question.delete(delete_all=True)
            if len(response.keys()) > 0:
                logger.error("Errors occured while deleting questions")
                for message in response:
                    logger.error(message, ":", response[message])

    def delete_questions_by_tdpname(self, tdp_name:TDPName) -> bool:
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_QUESTION} with name {tdp_name}")
        
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        logger.info(f"Number of vectors before deletion: {self.count_questions()}")

        error = False

        # https://docs.pinecone.io/guides/data/manage-rag-documents
        for ids in self.index_question.list(prefix=tdp_name.filename):
            response:dict = self.index_question.delete(ids)

            if len(response.keys()) > 0:
                error = True
                logger.error("Errors occured while deleting questions")
                for message in response:
                    logger.error(message, ":", response[message])
        
        logger.info(f"Number of vectors  after deletion: {self.count_questions()}")

        return error

    def count_questions(self) -> int:
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        return self.index_question.describe_index_stats().total_vector_count

    """ Development. Basic implementation """
    
    def store_item(self, id:str, dense_vector:np.ndarray, sparse_vector:coo_array, metadata:dict=None) -> None:
        if self.index_development is None:
            self.index_development = self.client.Index(self.INDEX_NAME_DEVELOPMENT)
                
        sparse_vector = SparseValues(indices=sparse_vector.col.tolist(), values=sparse_vector.data.tolist())
        vector = Vector(id=id, values=dense_vector.tolist(), sparse_values=sparse_vector, metadata=metadata)

        self.index_development.upsert([vector])

    def query_items(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=100, filter:dict=None, include_metadata=True):
        logger.info(f"Querying index {self.INDEX_NAME_DEVELOPMENT}")
        if self.index_development is None:
            self.index_development = self.client.Index(self.INDEX_NAME_DEVELOPMENT)
        
        t_start = time.time()
        response:QueryResponse = self.index_development.query(
            vector=dense_vector.tolist(),
            sparse_vector={'indices':sparse_vector.col.tolist(), 'values':sparse_vector.data.tolist()},
            top_k=limit,
            include_metadata=include_metadata,
            filter=filter
        )
        t_stop = time.time()

        logger.info(f"Index queried. Duration: {t_stop-t_start:.2f}s")
        return response

    def delete_items(self):
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_DEVELOPMENT}")
        
        if self.index_development is None:
            self.index_development = self.client.Index(self.INDEX_NAME_DEVELOPMENT)
        
        # if there actually are entries in the index
        if 0 < self.index_development.describe_index_stats().total_vector_count:
            response:dict = self.index_development.delete(delete_all=True)
            if len(response.keys()) > 0:
                logger.error(f"Errors occured while deleting from index {self.INDEX_NAME_DEVELOPMENT}")
                for message in response:
                    logger.error(message, ":", response[message])

    def count_items(self) -> int:
        if self.index_development is None:
            self.index_development = self.client.Index(self.INDEX_NAME_DEVELOPMENT)
        
        return self.index_development.describe_index_stats().total_vector_count


    """ Other """

    def reset_everything(self, embedding_size:int=1536) -> None:
        pass

if __name__ == "__main__":
    dotenv.load_dotenv()
    client = PineconeClient(os.getenv("PINECONE_API_KEY"))
    client.reset_everything()