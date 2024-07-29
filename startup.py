# System libraries
import os
import sys
sys.path.append(os.path.dirname(__file__))
# Third party libraries
from dotenv import load_dotenv
load_dotenv()
# Local libraries
from data_access.metadata.metadata_client import MongoDBClient as MetadataClient
from data_access.file.file_client import AzureFileClient, LocalFileClient
from data_access.vector.pinecone_client import PineconeClient
from data_access.cache.cache_client import MongoDBClient as CacheClient
from MyLogger import logger
from simple_profiler import SimpleProfiler

metadata_client = None
file_client = None
vector_client = None
cache_client = None
profiler = SimpleProfiler()

def get_clients() -> tuple[MetadataClient, AzureFileClient|LocalFileClient, PineconeClient]:
    # TODO remove this function in favor of individual client getters
    global metadata_client, file_client, vector_client

    if metadata_client is not None and file_client is not None and vector_client is not None:
        return metadata_client, file_client, vector_client

    profiler.start("[get_clients] get environment")

    ENVIRONMENT:str = get_environment()
    logger.info(f"ENVIRONMENT : {ENVIRONMENT}")

    profiler.start("[get_clients] initialize file client")
    if ENVIRONMENT == "LOCAL":
        file_client = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
    elif ENVIRONMENT == "AZURE":
        file_client = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))

    profiler.start("[get_clients] initialize metadata client")
    metadata_client = MetadataClient(os.getenv("MONGODB_CONNECTION_STRING"))

    profiler.start("[get_clients] initialize vector client")
    vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))

    profiler.stop()
    
    logger.info(profiler.print_statistics())
    logger.info("Clients initialized successfully")

    return metadata_client, file_client, vector_client

def get_metadata_client() -> MetadataClient:
    global metadata_client

    if metadata_client is not None:
        return metadata_client

    ENVIRONMENT:str = get_environment()

    metadata_client = MetadataClient(os.getenv("MONGODB_CONNECTION_STRING"))

    logger.info(f"Metadata client for environment {ENVIRONMENT} initialized successfully")

    return metadata_client

def get_file_client() -> AzureFileClient|LocalFileClient:
    global file_client

    if file_client is not None:
        return file_client

    ENVIRONMENT:str = get_environment()

    if ENVIRONMENT == "LOCAL":
        file_client = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
    elif ENVIRONMENT == "AZURE":
        file_client = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))

    logger.info(f"File client for environment {ENVIRONMENT} initialized successfully")

    return file_client

def get_vector_client() -> PineconeClient:
    global vector_client

    if vector_client is not None:
        return vector_client

    ENVIRONMENT:str = get_environment()

    vector_client = PineconeClient(os.getenv("PINECONE_API_KEY"))

    logger.info(f"Vector client for environment {ENVIRONMENT} initialized successfully")

    return vector_client

def get_cache_client() -> CacheClient:
    global cache_client

    if cache_client is not None:
        return cache_client

    ENVIRONMENT:str = get_environment()

    cache_client = CacheClient(os.getenv("MONGODB_CONNECTION_STRING"))

    logger.info(f"Cache client for environment {ENVIRONMENT} initialized successfully")

    return cache_client

def get_environment() -> str:
    ENVIRONMENT = os.getenv("ENVIRONMENT")
    if ENVIRONMENT is None: ENVIRONMENT = "LOCAL"
    ENVIRONMENT = ENVIRONMENT.upper()

    if ENVIRONMENT not in ["LOCAL", "AZURE"]:
        raise ValueError("Invalid environment")
    return ENVIRONMENT

logger.info(f"ENVIRONMENT : {get_environment()}")