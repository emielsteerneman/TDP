# System libraries
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
from data_access.file.file_client import LocalFileClient, AzureFileClient
from data_structures.TDPName import TDPName

local_file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
azure_file_client:AzureFileClient = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))

afn, ahash = zip(*map(lambda f: [f['name'], base64.b64encode(f['content_settings']['content_md5']).decode('ASCII')], azure_file_client.list_pdfs()))
amap = dict(zip(ahash, afn))
lfn, lhash = zip(*map(lambda f: [f.filename, local_file_client.get_pdf_hash(f)], local_file_client.list_pdfs()))
lmap = dict(zip(lhash, lfn))

tdp_names = [TDPName.from_filepath(fn) for fn in lfn]
team_names = set([tdp_name.team_name.name for tdp_name in tdp_names])
team_names = sorted(list(team_names))
print("Team names:")
print("\n".join(team_names))

exit()

print(f"Number of files in Azure: {len(ahash)}")
print(f"Number of files on local: {len(lhash)}")
print()

a_missing = [lmap[lhash] for lhash in lhash if lhash not in ahash]
l_missing = [amap[ahash] for ahash in ahash if ahash not in lhash]

print(f"Number of files missing in Azure: {len(a_missing)}")
print(f"Number of files missing on local: {len(l_missing)}")
print()

print( "\n".join( a_missing ) )

exit()


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



