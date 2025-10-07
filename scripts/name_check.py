# System libraries
from itertools import count
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import hashlib
import json
import base64
import subprocess
# Third party libraries
from dotenv import load_dotenv
load_dotenv()
# Local libraries
from data_access.file.file_client import LocalFileClient
from data_structures.TDPName import TDPName
local_file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))

local_files_pdf, local_hashes_pdf = local_file_client.list_pdfs()

name_league_map = {}
for f in local_files_pdf:
    if f.team_name.name not in name_league_map:
        name_league_map[f.team_name.name] = []
    name_league_map[f.team_name.name].append(f.league.name)

# sslteams = [ n for n, f in name_league_map.items() if "soccer_smallsize" in f]
sslteams = [ n for n, f in name_league_map.items() if "soccer_humanoid_adult" in f]
print(sorted(sslteams))

def similarity(name_a, name_b):
    abc = "abcdefghijklmnopqrstuvwxyz"
    count_a = [ name_a.lower().count(c) for c in abc]
    count_b = [ name_b.lower().count(c) for c in abc]
    score = 0
    for a, b in zip(count_a, count_b):
        if a != 0 and b != 0:
        # if b != 0:
            score += 1 if a == b else -1

    # if name_a == "PUMAS" and "p" in name_b.lower():
    #     print("?", score, name_b)

    return score

    # for window in range(1, 3):
    #     chars = set(a[::window])
    #     print(chars)

# print(similarity("triton fc", "tritonbots rcts"))
# exit()
    # return sum([ 1 if a == b else -1 for a, b in zip(count_a, count_b)])

# parse all filenames in ./todos
tdps_new = []
for filename in os.listdir("./todos/TDPs_2025/humanoid_adult"):
    tdpname = TDPName.from_filepath(filename)
    tdps_new.append(tdpname)
tdps_new.sort(key=lambda tdp: tdp.team_name.name)


for tdp in tdps_new:
    team, league = tdp.team_name.name, tdp.league.name
    if team in name_league_map:
        if league in name_league_map[team]:
            # print(f"{team.rjust(30)} - Valid")
            continue
        else:
            print(f"{team.rjust(30)} - Valid in different league")
    else:
        print(f"{team.rjust(30)} - Invalid")
        similarities = []
        for name in name_league_map:
            similarities.append((similarity(team, name), name))
        similarities.sort(reverse=True)
        for sscore, sname in similarities[:3]:
            print("".rjust(34), f"{sscore} {sname}")
            
        