# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Third party libraries
from dotenv import load_dotenv
load_dotenv()
# Local libraries
from data_access.metadata.metadata_client import MongoDBClient
from data_access.file.file_client import LocalFileClient
from data_structures.TDPName import TDPName
from data_structures.TDP import TDP
from extraction import extractor
from MyLogger import logger

metadata_client:MongoDBClient = MongoDBClient("mongodb://localhost:27017/")
file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))

pdfs = file_client.list_pdfs()
print(f"Found len(pdfs) PDFs")
for i_pdf, pdf in enumerate(pdfs):
    print(f"Processing PDF {i_pdf+1}/{len(pdfs)}")
    tdp:TDP = extractor.process_pdf(pdf)
    metadata_client.insert_tdp(tdp)