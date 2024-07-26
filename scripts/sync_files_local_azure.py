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

def local_to_azure(is_pdf:bool=True, force:bool=False, dry=False):
    if is_pdf:
        az_files, az_hashes = azure_file_client.list_pdfs()
        local_files, local_hashes = local_file_client.list_pdfs()

    else:
        az_files, az_hashes = azure_file_client.list_htmls()
        local_files, local_hashes = local_file_client.list_htmls()

    print(f"Number of files on local: {len(local_hashes)}")
    print(f"Number of files in Azure: {len(az_hashes)}")

    az_hashmap = dict(zip(az_hashes, az_files))
    local_hashmap = dict(zip(local_hashes, local_files))

    # For each file on local
    for local_hash in local_hashes:
        tdpname_local = local_hashmap[local_hash]
        
        # File is present in Azure
        if local_hash in az_hashmap:
            tdpname_azure = az_hashmap[local_hash]

            # Filenames match
            if tdpname_local == tdpname_azure: continue
            
            # File has conflicting filenames
            print(f"File with hash {local_hash} has conflicting filenames")
            print(f"  Azure: {tdpname_local}")
            print(f"  Local: {tdpname_azure}")

            # Don't fix the conflict
            if dry or not force: continue

            # Fix the conflict by removing the file from Azure
            print(f"Deleting file with hash {local_hash} from Azure... {tdpname_azure}")
            if is_pdf:
                azure_file_client.delete_pdf(tdpname_azure)
            else:
                azure_file_client.delete_html(tdpname_azure)

        # File is not present in Azure, upload it
        print(f"Uploading file with hash {local_hash} to Azure... {tdpname_local}")
        if not dry:
            if is_pdf:
                filepath = local_file_client.get_pdf(tdpname_local)
                azure_file_client.store_pdf(filepath, tdpname_local)
            else:
                filepath = local_file_client.get_html(tdpname_local)
                azure_file_client.store_html(filepath, tdpname_local)

def azure_to_local(is_pdf:bool=True, force:bool=False, dry=False):
    if is_pdf:
        az_files, az_hashes = azure_file_client.list_pdfs()
        local_files, local_hashes = local_file_client.list_pdfs()
    else:
        az_files, az_hashes = azure_file_client.list_htmls()
        local_files, local_hashes = local_file_client.list_htmls()

    print(f"Number of files on local: {len(local_hashes)}")
    print(f"Number of files in Azure: {len(az_hashes)}")

    az_hashmap = dict(zip(az_hashes, az_files))
    local_hashmap = dict(zip(local_hashes, local_files))

    # For each file on Azure
    for az_hash in az_hashes:
        tdpname_azure = az_hashmap[az_hash]

        # File is present on local
        if az_hash in local_hashmap:
            tdpname_local = local_hashmap[az_hash]

            # Filenames match
            if az_hashmap[az_hash] == local_hashmap[az_hash]: continue
            
            # File has conflicting filenames
            print(f"File with hash {az_hash} has conflicting filenames")
            print(f"  Azure: {tdpname_azure}")
            print(f"  Local: {tdpname_local}")

            # Don't fix the conflict
            if dry or not force: continue

            # Fix the conflict by removing the file from local
            print(f"Deleting file with hash {az_hash} from local... {tdpname_local}")
            if is_pdf:
                local_file_client.delete_pdf(tdpname_local)
            else:
                local_file_client.delete_html(tdpname_local)
        
        # File is not present on local
        print(f"Downloading file with hash {az_hash} from Azure... {tdpname_azure}")
        if not dry:
            if is_pdf:
                filebytes = azure_file_client.get_pdf_as_bytes(tdpname_azure)
                local_file_client.store_pdf_from_bytes(filebytes, tdpname_azure)
            else:
                filebytes = azure_file_client.get_html_as_bytes(tdpname_azure)
                local_file_client.store_html_from_bytes(filebytes, tdpname_azure)

def get_hashes_from_azure():
    print("Getting hashes from Azure...")
    command = "az storage blob list --account-name tdps -c tdps --query '[].[name, properties.contentSettings.contentMd5]'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL).decode("utf-8")
    output = json.loads(output)
    output = [ (x[0], x[1]) for x in output if x[1] is not None ]
    print(f"Received {len(output)} hashes from Azure.")
    return output

if __name__ == "__main__":
    print("Utility to sync local to Azure or vice versa")
    print("  pass --dry to not sync anything")
    print()

    dry = '--dry' in sys.argv

    while True:
        try:
            print("1. Sync local PDFs to Azure")
            print("2. Sync Azure PDFs to local")
            print("3. Sync local HTMLs to Azure")
            print("4. Sync Azure HTMLs to local")
            print()
            choice = int(input("Enter choice: "))
            force:bool = input("Force fix conflicts? (y/n): ") == "y"

            if choice == 1:
                local_to_azure(is_pdf=True, force=force, dry=dry)
            elif choice == 2:
                azure_to_local(is_pdf=True, force=force, dry=dry)
            elif choice == 3:
                local_to_azure(is_pdf=False, force=force, dry=dry)
            elif choice == 4:
                azure_to_local(is_pdf=False, force=force, dry=dry)
            else:
                print("Invalid choice")
            print("\n")
        except Exception as e:
            # TODO remove try except?
            raise e