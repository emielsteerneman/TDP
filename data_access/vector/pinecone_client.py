# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Third party libraries
import dotenv
import numpy as np
from pinecone import Pinecone, Vector, SparseValues, UpsertResponse, QueryResponse
from scipy.sparse import coo_array
# Local libraries
from data_access.vector.client_interface import ClientInterface
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.Sentence import Sentence
from data_structures.TDPName import TDPName
from MyLogger import logger
from uniqid import uniqid

class PineconeClient(ClientInterface):

    INDEX_NAME_PARAGRAPH = "paragraph"
    INDEX_NAME_QUESTION = "question"

    def __init__(self, api_key:str) -> None:
        logger.info("Initializing Pinecone client")
        self.client = Pinecone(api_key=api_key)
        self.index_paragraph = None
        self.index_question = None

    """ Paragraph chunks """

    def get_paragraph_chunks_metadata_by_id(self, ids:list[str]) -> list[dict]:
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        response = self.index_paragraph.fetch(ids)
        
        # for vector in response['vectors']:
        #     vector:Vector = response['vectors'][vector]
        #     print(vector.metadata)

        metadatas = [vector.metadata for vector in response['vectors'].values()]

        return metadatas

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

    def query_paragraphs(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=10, filter=None, include_metadata=True) -> list[Paragraph]:
        logger.info(f"Querying index {self.INDEX_NAME_PARAGRAPH}")
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        response:QueryResponse = self.index_paragraph.query(
            vector=dense_vector.tolist(),
            sparse_vector={'indices':sparse_vector.col.tolist(), 'values':sparse_vector.data.tolist()},
            top_k=limit,
            include_metadata=include_metadata,
            filter=filter
        )

        return response

    def delete_paragraphs(self):
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

    def delete_paragraphs_by_name(self, tdp_name:TDPName):
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_PARAGRAPH} with name {tdp_name}")
        
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        logger.info(f"Number of vectors before deletion: {self.count_paragraphs()}")

        # https://docs.pinecone.io/guides/data/manage-rag-documents
        for ids in self.index_paragraph.list(prefix=tdp_name.filename):
            response:dict = self.index_paragraph.delete(ids)

            if len(response.keys()) > 0:
                logger.error("Errors occured while deleting paragraphs")
                for message in response:
                    logger.error(message, ":", response[message])

        logger.info(f"Number of vectors  after deletion: {self.count_paragraphs()}")

    def count_paragraphs(self) -> int:
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        return self.index_paragraph.describe_index_stats().total_vector_count

    """ Questions """

    def get_questions_metadata_by_id(self, ids:list[str]) -> list[dict]:
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        response = self.index_question.fetch(ids)
        
        metadatas = [vector.metadata for vector in response['vectors'].values()]

        return metadatas

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
            'year': chunk.tdp_name.year
        }
        sparse_vector = SparseValues(indices=sparse_vector.col.tolist(), values=sparse_vector.data.tolist())
        vector = Vector(id=vector_id, values=dense_vector.tolist(), sparse_values=sparse_vector, metadata=metadata)

        self.index_question.upsert([vector])

    def query_questions(self, dense_vector:np.ndarray, sparse_vector:coo_array, limit:int=10, filter=None, include_metadata=True) -> list[ParagraphChunk]:
        logger.info(f"Querying index {self.INDEX_NAME_QUESTION}")
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        response:QueryResponse = self.index_question.query(
            vector=dense_vector.tolist(),
            sparse_vector={'indices':sparse_vector.col.tolist(), 'values':sparse_vector.data.tolist()},
            top_k=limit,
            include_metadata=include_metadata,
            filter=filter
        )

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

    def delete_questions_by_name(self, tdp_name:TDPName):
        logger.info(f"Deleting all vectors from index {self.INDEX_NAME_QUESTION} with name {tdp_name}")
        
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        logger.info(f"Number of vectors before deletion: {self.count_questions()}")

        # https://docs.pinecone.io/guides/data/manage-rag-documents
        for ids in self.index_question.list(prefix=tdp_name.filename):
            response:dict = self.index_question.delete(ids)

            if len(response.keys()) > 0:
                logger.error("Errors occured while deleting questions")
                for message in response:
                    logger.error(message, ":", response[message])
        
        logger.info(f"Number of vectors  after deletion: {self.count_questions()}")

    def count_questions(self) -> int:
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        return self.index_question.describe_index_stats().total_vector_count

    """ Other """

    def reset_everything(self, embedding_size:int=1536) -> None:
        pass

if __name__ == "__main__":
    dotenv.load_dotenv()
    client = PineconeClient(os.getenv("PINECONE_API_KEY"))
    client.reset_everything()