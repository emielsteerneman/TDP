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
from data_structures.TDPStructure import TDPStructure
from extraction import extractor
from MyLogger import logger

import startup
# metadata_client, file_client = startup.get_clients()

# pdfs = file_client.list_pdfs()

# pdf = pdfs[0]
# pdf_path = file_client.get_pdf(pdf)

pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/smallsize/2023/soccer_smallsize__2023__RoboTeam_Twente__0.pdf"
# pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/rescue/robot/2022/rescue_robot__2022__BART_LAB__0.pdf"

processed = extractor.process_pdf(pdf_path)

print(processed.outline())
