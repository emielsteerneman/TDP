# System libraries
import os
import sys
sys.path.append(os.path.dirname(__file__))
# Third party libraries
from custom_dotenv import load_dotenv
load_dotenv()
# Local libraries
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import AzureFileClient, LocalFileClient
from MyLogger import logger

metadata_client = None
file_client = None

def get_clients() -> tuple[MongoDBClient, AzureFileClient|LocalFileClient]:

    global metadata_client, file_client

    if metadata_client is not None and file_client is not None:
        return metadata_client, file_client

    ENVIRONMENT:str = get_environment()

    if ENVIRONMENT == "LOCAL":
        metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
        file_client = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
    elif ENVIRONMENT == "AZURE":
        metadata_client = MongoDBClient(os.getenv("MONGODB_CONNECTION_STRING"))
        file_client = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))

    logger.info("Clients initialized successfully")

    return metadata_client, file_client

def get_environment() -> str:
    ENVIRONMENT = os.getenv("ENVIRONMENT")
    if ENVIRONMENT is None: ENVIRONMENT = "LOCAL"
    ENVIRONMENT = ENVIRONMENT.upper()

    if ENVIRONMENT not in ["LOCAL", "AZURE"]:
        raise ValueError("Invalid environment")
    return ENVIRONMENT

logger.info(f"ENVIRONMENT : {get_environment()}")