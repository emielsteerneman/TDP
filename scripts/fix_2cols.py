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

file_client:LocalFileClient = startup.get_file_client()

col2 = [
    "soccer_smallsize__2010__Khainui__0",
    "soccer_simulation_3d__2017__BehRobot__0", 
    "soccer_simulation_3d__2016__BehRobot__0", 
    "industrial_atwork__2024__SRB__0"
    "soccer_humanoid_teen__2006__IranFanAvaran__0"
]

pdfs, _ = file_client.list_pdfs()
pdfs = [ pdf.filename for pdf in pdfs if "rescue" not in pdf.filename and pdf.filename not in blacklist and pdf.filename not in col2 ]

# tdp_name = TDPName.from_filepath("soccer_simulation_3d__2010__Apollo__0")
# pdf_path = file_client.get_pdf(tdp_name, no_copy=True)
# tdp_structure = extractor.process_pdf(pdf_path)
# print(tdp_structure)
# exit()



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
] + pdfs[:200]

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

scatter_1col_hits = []
scatter_1col_top1 = []
scatter_1col_top2 = []
scatter_1col_tm1 = []
scatter_1col_tm2 = []

for i_pdf, pdf in enumerate(pdfs_1):
    try:
        print("Processing", i_pdf)
        tdp_name = TDPName.from_string(pdf)
        pdf_path = file_client.get_pdf(tdp_name, no_copy=True)
        f_hits, top1, top2 = extractor.process_pdf(pdf_path)

        if f_hits < 0.15:
            print("???")
            print(pdf)
            input()

        scatter_1col_hits.append((f_hits, i_pdf))
        scatter_1col_top1.append((top1, i_pdf))
        scatter_1col_top2.append((top2, i_pdf))
        
    except Exception as e:
        pass

scatter_2col_hits = []
scatter_2col_top1 = []
scatter_2col_top2 = []
scatter_2col_tm1 = []
scatter_2col_tm2 = []

for i_pdf, pdf in enumerate(pdfs_2):
    try:
        tdp_name = TDPName.from_string(pdf)
        pdf_path = file_client.get_pdf(tdp_name, no_copy=True)
        f_hits, top1, top2 = extractor.process_pdf(pdf_path)

        scatter_2col_hits.append((f_hits, i_pdf))
        scatter_2col_top1.append((top1, i_pdf))
        scatter_2col_top2.append((top2, i_pdf))
    except Exception as e:
        pass

min_hits_1col = min([ f for f, _ in scatter_1col_hits ])
max_hits_2col = max([ f for f, _ in scatter_2col_hits ])

print(f"{max_hits_2col:.2f} < T < {min_hits_1col:.2f}")



plt.scatter(*zip(*scatter_1col_hits), marker='x', color='orange', label="1 column")
plt.scatter(*zip(*scatter_2col_hits), color='darkblue', label="2 columns")
plt.legend()
plt.show()

plt.scatter(*zip(*scatter_1col_top1), marker='x', color='orange', label="1 column")
plt.scatter(*zip(*scatter_1col_top2), marker='x', color='red', label="1 column")
plt.scatter(*zip(*scatter_2col_top1), color='blue', label="2 columns")
plt.scatter(*zip(*scatter_2col_top2), color='darkblue', label="2 columns")
plt.legend()
plt.show()