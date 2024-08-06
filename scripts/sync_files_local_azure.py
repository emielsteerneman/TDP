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

local_file_client:LocalFileClient = LocalFileClient(os.getenv("LOCAL_FILE_ROOT"))
azure_file_client:AzureFileClient = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))

def status(list_some:bool=False, list_all:bool=False):
    index_stop:int = 5 if list_some else 999999999

    az_files_pdf, az_hashes_pdf = azure_file_client.list_pdfs()
    local_files_pdf, local_hashes_pdf = local_file_client.list_pdfs()
    az_files_html, az_hashes_html = azure_file_client.list_htmls()
    local_files_html, local_hashes_html = local_file_client.list_htmls()

    local_duplicates_pdf = len(local_hashes_pdf) - len(list(set(local_hashes_pdf)))
    local_duplicates_html = len(local_hashes_html) - len(list(set(local_hashes_html)))

    local_hashmap_pdf = dict(zip(local_hashes_pdf, local_files_pdf))
    az_hashmap_pdf = dict(zip(az_hashes_pdf, az_files_pdf))
    local_hashmap_html = dict(zip(local_hashes_html, local_files_html))
    az_hashmap_html = dict(zip(az_hashes_html, az_files_html))

    missing_hashes_on_local_pdf = list(set(az_hashes_pdf) - set(local_hashes_pdf))
    missing_hashes_on_azure_pdf = list(set(local_hashes_pdf) - set(az_hashes_pdf))
    missing_hashes_on_local_html = list(set(az_hashes_html) - set(local_hashes_html))
    missing_hashes_on_azure_html = list(set(local_hashes_html) - set(az_hashes_html))

    pdfs_missing_htmls = list(set([_.filename for _ in local_files_pdf]) - set([_.filename for _ in local_files_html]))
    htmls_missing_pdfs = list(set([_.filename for _ in local_files_html]) - set([_.filename for _ in local_files_pdf]))

    ### Find duplicates
    duplicates_pdf = []
    if local_duplicates_pdf:
        for i_hash, hash in enumerate(local_hashes_pdf):
            sub_duplicates = [local_files_pdf[i+i_hash] for i, h in enumerate(local_hashes_pdf[i_hash:]) if h == hash]
            if 1 < len(sub_duplicates):
                duplicates_pdf.append(sub_duplicates)
    duplicates_html = []
    if local_duplicates_html:
        for i_hash, hash in enumerate(local_hashes_html):
            sub_duplicates = [local_files_html[i+i_hash] for i, h in enumerate(local_hashes_html[i_hash:]) if h == hash]
            if 1 < len(sub_duplicates):
                duplicates_html.append(sub_duplicates)

    ### Find conflicts
    conflicts_pdf = []
    conflicts_html = []

    # For each PDF file on local
    for local_hash in local_hashes_pdf:
        tdpname_local = local_hashmap_pdf[local_hash]
        
        # File is present in Azure
        if local_hash in az_hashmap_pdf:
            tdpname_azure = az_hashmap_pdf[local_hash]

            # Filenames match
            if tdpname_local == tdpname_azure: continue
            
            # File has conflicting filenames
            conflicts_pdf.append((tdpname_local, tdpname_azure))

    # For each HTML file on local
    for local_hash in local_hashes_html:
        tdpname_local = local_hashmap_html[local_hash]
        
        # File is present in Azure
        if local_hash in az_hashmap_html:
            tdpname_azure = az_hashmap_html[local_hash]

            # Filenames match
            if tdpname_local == tdpname_azure: continue

            # File has conflicting filenames            
            conflicts_html.append((tdpname_local, tdpname_azure))
            
    print("\n\nStatus:\n")
    print(f"PDFs  on local: {len(local_hashes_pdf)} ({local_duplicates_pdf} duplicates)")
    print(f"PDFs  in Azure: {len(az_hashes_pdf)}")
    print()
    print(f"HTMLs on local: {len(local_hashes_html)} ({local_duplicates_html} duplicates)")
    print(f"HTMLs in Azure: {len(az_hashes_html)}")
    print()

    print(f"PDFs  missing on local: {len(missing_hashes_on_local_pdf)}")
    print(f"PDFs  missing on Azure: {len(missing_hashes_on_azure_pdf)}")
    print()
    print(f"HTMLs missing on local: {len(missing_hashes_on_local_html)}")
    print(f"HTMLs missing on Azure: {len(missing_hashes_on_azure_html)}")
    print()

    print(f"PDFs  missing HTMLs: {len(pdfs_missing_htmls)}")
    print(f"HTMLs missing PDFs : {len(htmls_missing_pdfs)}")

    print(f"Number of conflicts in PDFs : {len(conflicts_pdf)}")
    print(f"Number of conflicts in HTMLs: {len(conflicts_html)}")
    print()

    if list_some or list_all:
        if 0 < len(missing_hashes_on_local_pdf):
            print("PDFs  missing on local:")
            for i, hash in enumerate(missing_hashes_on_local_pdf[:index_stop]):
                print(f"  {i:4} {hash} : {az_hashmap_pdf[hash]}")
            print()
        if 0 < len(missing_hashes_on_azure_pdf):
            print("PDFs  missing on Azure:")
            for i, hash in enumerate(missing_hashes_on_azure_pdf[:index_stop]):
                print(f"  {i:4} {hash} : {local_hashmap_pdf[hash]}")
            print()

        if 0 < len(missing_hashes_on_local_html):
            print("HTMLs missing on local:")
            for i, hash in enumerate(missing_hashes_on_local_html[:index_stop]):
                print(f"  {i:4} {hash} : {az_hashmap_html[hash]}")
            print()
        if 0 < len(missing_hashes_on_azure_html):
            print("HTMLs missing on Azure:")
            for i, hash in enumerate(missing_hashes_on_azure_html[:index_stop]):
                print(f"  {i:4} {hash} : {local_hashmap_html[hash]}")
            print()

        if pdfs_missing_htmls:
            print("PDFs missing HTMLs:")
            for i, pdf in enumerate(pdfs_missing_htmls[:index_stop]):
                print(f"  {i:4} {pdf}")
            print()
        if htmls_missing_pdfs:
            print("HTMLs missing PDFs:")
            for i, html in enumerate(htmls_missing_pdfs[:index_stop]):
                print(f"  {i:4} {html}")
            print()

        if local_duplicates_pdf:
            print("Duplicate PDFs:")
            for i, duplicates in enumerate(duplicates_pdf[:index_stop]):
                for j, duplicate in enumerate(duplicates):
                    print(f"  {i:4} {j:4} {duplicate}")
                print()
        if local_duplicates_html:
            print("Duplicate HTMLs:")
            for i, duplicates in enumerate(duplicates_html[:index_stop]):
                for j, duplicate in enumerate(duplicates):
                    print(f"  {i:4} {j:4} {duplicate}")
                print()

        if 0 < len(conflicts_pdf):
            print("Conflicting PDFs:")
            for i, (local, azure) in enumerate(conflicts_pdf[:index_stop]):
                print(f"  {i:4} {local} : {azure}")
            print()
        if 0 < len(conflicts_html):
            print("Conflicting HTMLs:")
            for i, (local, azure) in enumerate(conflicts_html[:index_stop]):
                print(f"  {i:4} local : {local} <> azure : {azure}")
            print()
    print("\n")

def local_to_azure(is_pdf:bool=True, force:bool=False, dry=False):
    if is_pdf:
        az_files, az_hashes = azure_file_client.list_pdfs()
        local_files, local_hashes = local_file_client.list_pdfs()

    else:
        az_files, az_hashes = azure_file_client.list_htmls()
        local_files, local_hashes = local_file_client.list_htmls()

    print(f"Number of files on local: {len(local_hashes)} ({len(local_hashes) - len(list(set(local_hashes)))} duplicates)")
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
            print(f"  Azure: {tdpname_azure}")
            print(f"  Local: {tdpname_local}")

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
                azure_file_client.store_pdf(filepath, tdpname_local, overwrite=True)
            else:
                filepath = local_file_client.get_html(tdpname_local)
                azure_file_client.store_html(filepath, tdpname_local, overwrite=True)

def azure_to_local(is_pdf:bool=True, force:bool=False, dry=False):
    if is_pdf:
        az_files, az_hashes = azure_file_client.list_pdfs()
        local_files, local_hashes = local_file_client.list_pdfs()
    else:
        az_files, az_hashes = azure_file_client.list_htmls()
        local_files, local_hashes = local_file_client.list_htmls()

    print(f"Number of files on local: {len(local_hashes)} ({len(local_hashes) - len(list(set(local_hashes)))} duplicates)")
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
            print("1. Status")
            print("2. Sync local PDFs to Azure")
            print("3. Sync Azure PDFs to local")
            print("4. Sync local HTMLs to Azure")
            print("5. Sync Azure HTMLs to local")
            print()
            choice = int(input("Enter choice: "))
            if choice in [2, 3, 4, 5]:
                force:bool = input("Force fix conflicts? (y/n): ") == "y"

            if choice == 1:
                print("  1. Don't list")
                print("  2. List 5")
                print("  3. List all")
                print()
                subchoice = int(input("  Enter choice: "))
                status(list_some=subchoice == 2, list_all=subchoice == 3)
            elif choice == 2:
                local_to_azure(is_pdf=True, force=force, dry=dry)
            elif choice == 3:
                azure_to_local(is_pdf=True, force=force, dry=dry)
            elif choice == 4:
                local_to_azure(is_pdf=False, force=force, dry=dry)
            elif choice == 5:
                azure_to_local(is_pdf=False, force=force, dry=dry)
            else:
                print("Invalid choice")
            print("\n")
        except Exception as e:
            # TODO remove try except?
            raise e