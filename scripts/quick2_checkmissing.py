# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import hashlib
import utilities as U
import json
import base64
import subprocess

def get_hashes_from_azure():
    print("Getting hashes from Azure...")
    command = "az storage blob list --account-name tdps -c tdps --query '[].[name, properties.contentSettings.contentMd5]'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
    output = json.loads(output)
    output = [ (x[0], x[1]) for x in output if x[1] is not None ]
    print(f"Received {len(output)} hashes from Azure.")
    return output

hashes_az = get_hashes_from_azure()

tdps_az, hashes_az = zip(*hashes_az)

tdps_local_set1 = U.find_all_tdps("tdps")
tdps_local_set2 = U.find_all_tdps("/home/emiel/Desktop/projects/rust_tdp_scraper/TDPs")

hashes_local_set1 = [ ]
print("Calculating hashes local set 1...")
for tdp in tdps_local_set1:
    with open(tdp, "rb") as f:
        file_hash = base64.b64encode( hashlib.md5(f.read()).digest() ).decode('ASCII')
        hashes_local_set1.append(file_hash)

hashes_local_set2 = [ ]
print("Calculating hashes local set 2...")
for tdp in tdps_local_set2:
    with open(tdp, "rb") as f:
        file_hash = base64.b64encode( hashlib.md5(f.read()).digest() ).decode('ASCII')
        hashes_local_set2.append(file_hash)

# print("Checking if all files in local set 1 are in local set 2...")
# for i_hash_local, hash_local in enumerate(hashes_local_set1):
#     filepath = tdps_local_set1[i_hash_local]
#     if hash_local not in hashes_local_set2:
#         print(f"File {filepath} not found in local set 2")

# print("Checking if all files in local set 2 are in local set 1...")
# for i_hash_local, hash_local in enumerate(hashes_local_set2):
#     filepath = tdps_local_set2[i_hash_local]
#     if hash_local not in hashes_local_set1:
#         print(f"File {filepath} not found in local set 1")

# print("Checking if all files in Azure are in local set 1...")
# for i_hash_az, hash_az in enumerate(hashes_az):
#     filepath = tdps_az[i_hash_az]
#     if hash_az not in hashes_local_set1:
#         print(f"File {filepath} not found in local set 1")

print("Checking if all files in local set 1 are in Azure...")
for i_hash_local, hash_local in enumerate(hashes_local_set1):
    filepath = tdps_local_set1[i_hash_local]
    if hash_local not in hashes_az:
        print(f"File {filepath} not found in az set")

print("Checking if all files in local set 2 are in Azure...")
for i_hash_local, hash_local in enumerate(hashes_local_set2):
    filepath = tdps_local_set2[i_hash_local]
    if hash_local not in hashes_az:
        print(f"File {filepath} not found in az set")



