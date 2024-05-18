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
from data_structures.Paragraph import Paragraph
from extraction import extractor
from MyLogger import logger
import startup
from extract_pdf_tests import paragraph_tests

def process(pdf_path:str):

    tdp_structure:TDPStructure = extractor.process_pdf(pdf_path)

    paragraph_titles = [ paragraph.text_raw for paragraph in tdp_structure.paragraphs ]

    filename = os.path.basename(pdf_path)

    invalid, missing = [], []

    if filename in paragraph_tests:
        # If not equal, print the difference
        if paragraph_titles != paragraph_tests[filename]:
            
            for paragraph_title in paragraph_titles:
                if paragraph_title not in paragraph_tests[filename]:
                    logger.error(f"Invalid paragraph '{paragraph_title}'")
                    invalid.append(paragraph_title)

            for paragraph_title in paragraph_tests[filename]:
                if paragraph_title not in paragraph_titles:
                    logger.error(f"Missing paragraph '{paragraph_title}'")
                    missing.append(paragraph_title)
        else:
            print("Paragraphs are equal")    
    else:
        print(f"Missing test for {filename}")

    for paragraph in tdp_structure.paragraphs:
        print(f"{paragraph.sequence_id:3}: {paragraph.text_raw}")
        # print(paragraph.content_raw(), "\n\n")


    return invalid, missing


pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/smallsize/2023/soccer_smallsize__2023__RoboTeam_Twente__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/athome/domestic/2019/athome_domestic__2019__Austin_Villa__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/midsize/2010/soccer_midsize__2010__IsePorto__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/smallsize/2009/soccer_smallsize__2009__B-Smart__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/humanoid/kid/2019/soccer_humanoid_kid__2019__Ichiro__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/humanoid/teen/2019/soccer_humanoid_teen__2019__MRL__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/industrial/atwork/2021/industrial_atwork__2021___AutonOHM__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/simulation/2d/2022/soccer_simulation_2d__2022__FRA-UNIted__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/humanoid/adult/2019/soccer_humanoid_adult__2019__Tsinghua_Hephaestus__0.pdf"
pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/industrial/logistics/2019/industrial_logistics__2019__Solidus__0.pdf"
# pdf_path = "/home/emiel/Desktop/projects/tdp/static/pdf/soccer/simulation/3d/2019/soccer_simulation_3d__2019__FC_Portugal_3D__0.pdf"


results = {}

if True:
    # os.system(f"xdg-open {pdf_path}")
    invalid, missing = process(pdf_path)
    results[pdf_path] = {
        "invalid": invalid,
        "missing": missing
    }
else:
    for filename in paragraph_tests:
        print("\n\n")
        print(filename)
        tdpname = TDPName.from_filepath(filename)
        filepath = f"/home/emiel/Desktop/projects/tdp/static/pdf/{tdpname.to_filepath()}"
        invalid, missing = process(filepath)
        results[filename] = {
            "invalid": invalid,
            "missing": missing
        }

for filename in results:
    print()
    print(os.path.basename(filename))

    if os.path.basename(filename) not in paragraph_tests:
        print("No tests found for this file")
        continue

    invalid, missing = results[filename]["invalid"], results[filename]["missing"]
    if len(invalid) > 0:
        print("Invalid:")
        for paragraph in invalid:
            print(f"  '{paragraph}'")
    if len(missing) > 0:
        print("Missing:")
        for paragraph in missing:
            print(f"  '{paragraph}'")

    if len(invalid) == 0 and len(missing) == 0:
        print("All tests passed")
