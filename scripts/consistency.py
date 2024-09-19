# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import time
# Third party libraries
# Local libraries
import startup
from data_structures.TDPName import TDPName

file_client = startup.get_file_client()
metadata_client = startup.get_metadata_client()
vector_client = startup.get_vector_client()

local_names, local_hashes = file_client.list_pdfs()
metadata = metadata_client.find_tdps()

local_names_str = [ tdp_name.filename for tdp_name in local_names ]
metadata_names = [ tdp.tdp_name for tdp in metadata ]
metadata_names_str = [ tdp_name.filename for tdp_name in metadata_names ]
metadata_hashes = [ tdp.filehash for tdp in metadata ]

n_file_duplicates = len(local_hashes) - len(set(local_hashes))
n_metadata_duplicates = len(metadata_hashes) - len(set(metadata_hashes))

print(f"# of local files   : {len(local_hashes)} ({ n_file_duplicates } duplicates) ")
print(f"# of metadata files: {len(metadata_hashes)} ({ n_metadata_duplicates } duplicates)")

print("Entries in metadata not tied to a file: ")
# These should be removed
for i in range(len(metadata)):
    metadata_name, metadata_hash = metadata_names[i], metadata_hashes[i]
    metadata_name_in_files = metadata_name in local_names
    metadata_hash_in_files = metadata_hash in local_hashes                                                  

    if not metadata_name_in_files or not metadata_hash_in_files:
        # Find all related entries in vector database
        paragraph_chunk_ids = vector_client.get_paragraph_chunks_by_tdpname(metadata_name)
        question_ids = vector_client.get_questions_by_tdpname(metadata_name)

        print(f"  Hash={int(metadata_hash_in_files)} name={int(metadata_name_in_files)} #p={len(paragraph_chunk_ids):2} #q={len(question_ids):2}: {metadata_name}")

        # error = False
        # error |= vector_client.delete_paragraph_chunks_by_tdpname(metadata_name)
        # error |= vector_client.delete_questions_by_tdpname(metadata_name)
        # if not error: metadata_client.delete_tdp_by_name(metadata_name)

        # time.sleep(2)

        # paragraph_chunk_ids = vector_client.get_paragraph_chunks_by_tdpname(metadata_name)
        # question_ids = vector_client.get_questions_by_tdpname(metadata_name)
        # print(f"  Hash={int(metadata_hash_in_files)} name={int(metadata_name_in_files)} #p={len(paragraph_chunk_ids):2} #q={len(question_ids):2}: {metadata_name}")
        # print()        

print("Files not tied to an entry in metadata: ")
for i in range(len(local_names)):
    local_name, local_hash = local_names[i], local_hashes[i]
    local_name_in_metadata = local_name in metadata_names
    local_hash_in_metadata = local_hash in metadata_hashes

    if not local_name_in_metadata or not local_hash_in_metadata:
        print(f"  Hash={int(local_hash_in_metadata)} name={int(local_name_in_metadata)} : {local_name}")

# if n_metadata_duplicates:
#     for i_metadata_hash, metadata_hash in enumerate(metadata_hashes):
#         indices = [ i + i_metadata_hash for i, x in enumerate(metadata_hashes[i_metadata_hash:]) if x == metadata_hash ]
#         if 2 <= len(indices):
#             print(f"{len(indices)} duplicates")
#             for index in indices:
#                 hash_in_local = metadata_hashes[index] in local_hashes
#                 name_in_local = metadata_names_str[index] in local_names_str
#                 print(f"  Hash={int(hash_in_local)} name={int(name_in_local)} : {metadata_names[index]}")
