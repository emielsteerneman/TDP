# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Third party libraries
import dotenv
import numpy as np
from pinecone import Pinecone, Vector, SparseValues, UpsertResponse, QueryResponse
# Local libraries
from data_access.vector.client_interface import ClientInterface
from data_structures.Paragraph import Paragraph
from data_structures.ParagraphChunk import ParagraphChunk
from data_structures.Sentence import Sentence
from MyLogger import logger


class PineconeClient(ClientInterface):

    INDEX_NAME_PARAGRAPH = "paragraph"
    INDEX_NAME_QUESTION = "question"

    def __init__(self, api_key:str) -> None:
        logger.info("Initializing Pinecone client")
        self.client = Pinecone(api_key=api_key)
        self.index_paragraph = None
        self.index_question = None

    def store_paragraph(self, paragraph: Paragraph, collection: str) -> None:
        pass

    def store_sentence(self, sentence: Sentence, collection: str) -> None:
        pass

    def store_question(self, chunk: ParagraphChunk, question: str, dense_vector:np.ndarray, sparse_vector:dict) -> None:
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        vector_id = chunk.tdp_name.filename + "__" + str(chunk.paragraph_sequence_id) + "__" + str(chunk.sequence_id)
                
        metadata = {
            'question': question,
            'paragraph_sequence_id': chunk.paragraph_sequence_id,
            'chunk_sequence_id': chunk.sequence_id,
            
            'tdp_name': chunk.tdp_name.filename,
            'league': chunk.tdp_name.league.name,
            'team': chunk.tdp_name.team_name.name,
            'year': chunk.tdp_name.year
        }
        sparse_vector = SparseValues(indices=sparse_vector['indices'], values=sparse_vector['values'])
        vector = Vector(id=vector_id, values=dense_vector.tolist(), sparse_values=sparse_vector, metadata=metadata)

        self.index_question.upsert([vector])

    def store_paragraph_chunk(self, chunk: ParagraphChunk, dense_vector:np.ndarray, sparse_vector:dict) -> None:
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
            'league': chunk.tdp_name.league.name,
            'team': chunk.tdp_name.team_name.name,
            'year': chunk.tdp_name.year
        }
                
        sparse_vector = SparseValues(indices=sparse_vector['indices'], values=sparse_vector['values'])
        vector = Vector(id=vector_id, values=dense_vector.tolist(), sparse_values=sparse_vector, metadata=metadata)

        self.index_paragraph.upsert([vector])

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

    def query_paragraphs(self, dense_vector:np.ndarray, sparse_vector:dict, limit:int=10) -> list[Paragraph]:
        logger.info(f"Querying index {self.INDEX_NAME_PARAGRAPH}")
        if self.index_paragraph is None:
            self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)
        
        response:QueryResponse = self.index_paragraph.query(
            vector=dense_vector.tolist(),
            sparse_vector=sparse_vector,
            top_k=limit,
            include_metadata=True
        )

        # print(response)
        return response
    
    def query_questions(self, dense_vector:np.ndarray, sparse_vector:dict, limit:int=10) -> list[ParagraphChunk]:
        logger.info(f"Querying index {self.INDEX_NAME_QUESTION}")
        if self.index_question is None:
            self.index_question = self.client.Index(self.INDEX_NAME_QUESTION)
        
        response:QueryResponse = self.index_question.query(
            vector=dense_vector.tolist(),
            sparse_vector=sparse_vector,
            top_k=limit,
            include_metadata=True
        )

        # print(response)
        return response

    def reset_everything(self, embedding_size:int=1536) -> None:
        indices = self.client.list_indexes().names()
        # if self.INDEX_NAME_PARAGRAPH in indices:
        #     self.client.delete_index(self.INDEX_NAME_PARAGRAPH)

        # if self.INDEX_NAME_PARAGRAPH not in indices:
        #     logger.info(f"Creating index {self.INDEX_NAME_PARAGRAPH}")
        #     self.client.create_index(self.INDEX_NAME_PARAGRAPH, dimension=embedding_size)

        self.index_paragraph = self.client.Index(self.INDEX_NAME_PARAGRAPH)

        logger.info("Pinecone succesfully reset")

if __name__ == "__main__":
    dotenv.load_dotenv()
    client = PineconeClient(os.getenv("PINECONE_API_KEY"))
    client.reset_everything()