# System libraries
import os
import sys
sys.path.append(os.path.dirname(__file__))
# Third party libraries
from dotenv import load_dotenv
load_dotenv()
# Local libraries
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import AzureFileClient, LocalFileClient
from MyLogger import logger

def get_clients() -> tuple[MongoDBClient, AzureFileClient|LocalFileClient]:

    ENVIRONMENT = os.getenv("ENVIRONMENT").upper()
    if ENVIRONMENT is None: ENVIRONMENT = "LOCAL"

    if ENVIRONMENT not in ["LOCAL", "AZURE"]:
        raise ValueError("Invalid environment")

    logger.info(f"Environment: {ENVIRONMENT}")

    if ENVIRONMENT == "LOCAL":
        metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
        file_client = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
    elif ENVIRONMENT == "AZURE":
        metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
        file_client = AzureFileClient(os.getenv("AZURE_CONNECTION_STRING"))

    logger.info("Clients initialized successfully")

    return metadata_client, file_client