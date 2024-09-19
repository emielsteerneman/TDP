# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Third party libraries
import matplotlib.pyplot as plt
# Local libraries
import startup
from data_access.file.file_client import LocalFileClient
from data_structures.TDPName import TDPName
from data_structures.TDPStructure import TDPStructure
from extraction import extractor
from blacklist import blacklist




# levels = [1, 1, 3, 3, 3, 3, 3, 1, 2, 3, 3, 2, 3, 3, 1]
# for il, l in enumerate(levels):
#     print(f"{'|   ' * l}|- {l}_{il}")

# print("\n")

# current_level = 0
# for il, l in enumerate(levels):
#     if current_level + 1 < l:
#         l = current_level + 1
#     else:
#         current_level = l
#     print(f"{'|   ' * l}|- {l}_{il}")
# exit()

file_client:LocalFileClient = startup.get_file_client()

col2 = [
    "soccer_smallsize__2010__Khainui__0",
    "soccer_simulation_3d__2017__BehRobot__0", 
    "soccer_simulation_3d__2016__BehRobot__0", 
    "industrial_atwork__2024__SRB__0",
    "soccer_humanoid_teen__2006__IranFanAvaran__0"
]

pdfs, _ = file_client.list_pdfs()

# Parse all
for pdf in pdfs:
    try:
        pdf_path = file_client.get_pdf(pdf, no_copy=True)
        structure = extractor.process_pdf(pdf_path)
        for paragraph in structure.paragraphs:
            print(paragraph.text_raw, len(paragraph.content_raw().split(" ")))
    except Exception as e:
        print(e)
        pass
# exit()





tdp_name = TDPName.from_filepath("rescue_robot__2019__XFinder__0.pdf")
tdp_name = TDPName.from_filepath("soccer_smallsize__2024__RoboTeam_Twente__0.pdf")
pdf_path = file_client.get_pdf(tdp_name, no_copy=True)
tdp_structure = extractor.process_pdf(pdf_path)
print(tdp_structure)
exit()

pdfs = [ pdf.filename for pdf in pdfs if "rescue" not in pdf.filename and pdf.filename not in blacklist and pdf.filename not in col2 ]

pdfs_1 = [
    "rescue_robot__2013__AriAnA__0",
    "rescue_robot__2013__ASEMA-MASHIN__0",
    "rescue_robot__2013__BART_LAB_Rescue__0",
    "rescue_robot__2013__CASualty__0",
    "rescue_robot__2013__CUAS_RRR__0",
    "rescue_robot__2013__Cuerbot__0",
    "rescue_robot__2013__Hector_Darmstadt__0",
    "rescue_robot__2013__iRAP__0",
    "rescue_robot__2013__Jacobs__0",
    "rescue_robot__2013__Kauil-TecMTY__0",
    "rescue_robot__2013__MRL__0",
    "rescue_robot__2013__NIIT-BLUE__0",
    "rescue_robot__2013__PANDORA__0",
    "rescue_robot__2013__RKRS__0",
    "rescue_robot__2013__RoboEaters__0",
    "rescue_robot__2013__SEU__0",
    "rescue_robot__2013__SocRob__0",
    "rescue_robot__2013__STABILIZE__0",
    "rescue_robot__2013__UP-Robotics__0",
    "rescue_robot__2013__Warwick__0",
    "rescue_robot__2013__YILDIZ__0",
    "rescue_robot__2013__YRA__0",
    "rescue_robot__2015__BART_LAB_Rescue__0",
    "rescue_robot__2015__Hector_Darmstadt__0",
    "rescue_robot__2015__iRAP__0",
    "rescue_robot__2015__MRL__0",
    "rescue_robot__2015__PANDORA__0",
    "rescue_robot__2015__RRT-Team__0"
] + pdfs

pdfs_2 = [
    "rescue_robot__2019__ATR__0",
    "rescue_robot__2019__AutonOHM__0",
    "rescue_robot__2019__Club_Capra__0",
    "rescue_robot__2019__Hector_Darmstadt__0",
    "rescue_robot__2019__iRAP__0",
    "rescue_robot__2019__Mars-Rescue__0",
    "rescue_robot__2019__MRL__0",
    "rescue_robot__2019__NuBot__0",
    "rescue_robot__2019__RKRS__0",
    "rescue_robot__2019__SHINOBI__0",
    "rescue_robot__2019__Sroewground_Robot__0",
    "rescue_robot__2019__TecnoBot__0",
    "rescue_robot__2019__XFinder__0",
    "rescue_robot__2019__X-kau_ITNL__0",
    "rescue_robot__2022__BART_LAB_Rescue__0 ",
    "rescue_robot__2022__Club_Capra__0",
    "rescue_robot__2022__Hector_Darmstadt__0",
    "rescue_robot__2022__iRAP__0",
    "rescue_robot__2022__Nexis-R__0",
    "rescue_robot__2022__SHINOBI__0",
    "rescue_robot__2022__Team_DYNAMICS__0"
] + col2

for i_pdf, pdf in enumerate(pdfs_1[:200]):

    if pdf in pdfs_2: continue
    try:
        print("\n\n\nProcessing", i_pdf, pdf in pdfs_2, pdf)
        tdp_name = TDPName.from_string(pdf)
        pdf_path = file_client.get_pdf(tdp_name, no_copy=True)
        n_columns = extractor.process_pdf(pdf_path)

        if n_columns != 1:
            print("not 1???")
            print(pdf)
            # input()
        
    except Exception as e:
        print(e)
        pass

for i_pdf, pdf in enumerate(pdfs_2[:200]):
    try:
        print("\n\n\nProcessing", i_pdf, pdf)
        tdp_name = TDPName.from_string(pdf)
        pdf_path = file_client.get_pdf(tdp_name, no_copy=True)
        n_columns = extractor.process_pdf(pdf_path)

        if n_columns != 2:
            print("not 2???")
            print(pdf)
            # input()

    except Exception as e:
        print(e)
        pass