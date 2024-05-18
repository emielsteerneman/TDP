# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Third party libraries
import dotenv
from pinecone import Pinecone
# Local libraries
from data_access.vector.client_interface import ClientInterface
from data_structures.Paragraph import Paragraph
from data_structures.Sentence import Sentence


class PineconeClient(ClientInterface):

    def __init__(self, api_key:str) -> None:
        self.client = Pinecone(api_key=api_key)
        indices = self.client.list_indexes()
        print(indices)

    def store_sentence(self, sentence: Sentence, collection: str) -> None:
        pass

    def store_paragraph(self, paragraph: Paragraph, collection: str) -> None:
        # 40kb metadata limit
        pass

    def reset_everything(self) -> None:
        pass

if __name__ == "__main__":
    dotenv.load_dotenv()
    client = PineconeClient(os.getenv("PINECONE_API_KEY"))