# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from abc import ABC, abstractmethod
# Third party libraries
from azure.storage.blob import BlobServiceClient
# Local libraries
from data_structures.TDPName import TDPName

class FileManager(ABC):
    
    @abstractmethod
    def store_pdf(filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        raise NotImplementedError

    def list_pdfs(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def delete_pdf():
        raise NotImplementedError

    @abstractmethod
    def pdf_exists(tdp_name:TDPName):
        raise NotImplementedError

class AzureFileManager(FileManager):

    def __init__(self, connection_string:str):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client("tdps")

    def store_pdf(filepath_in:str, overwrite:bool=False):
        pass

    def list_pdfs(self) -> list[str]:
        pdfs = self.container_client.list_blobs()
        pdfs = [ pdf for pdf in pdfs if pdf.name.endswith(".pdf") ]
        # TODO remove this hack
        pdfs = [ pdf for pdf in pdfs if "misc" not in pdf.name ]
        # pdfs = [ TDPName.from_filepath(pdf.name) for pdf in pdfs ]
        return pdfs

    def delete_pdf():
        pass

    def pdf_exists(tdp_name:TDPName):
        pass
    
class LocalFileManager(FileManager):
    def __init__(self, root_dir:str):
        if not os.path.isdir(root_dir):
            os.mkdir(root_dir)
        
        self.root_dir:str = root_dir
            
    def store_pdf(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        if self.pdf_exists(tdp_name) and not (overwrite or increment_index):
            raise FileExistsError(f"File {tdp_name} already exists")

    def delete_pdf(self, tdp_name:TDPName):
        filepath:str = os.path.join(self.root_dir, tdp_name.filename)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File {tdp_name} does not exist")
        os.remove(filepath)

    def list_pdfs(self) -> list[str]:
        pdfs = []
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".pdf"):
                    filepath = os.path.join(root, file)
                    # TODO remove this hack
                    if "misc" in filepath: continue
                    pdfs.append(filepath)
        return pdfs

    def pdf_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.root_dir, tdp_name.filename)
        return os.path.isfile(filepath)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    manager = LocalFileManager("tdps")
    print(f"{len(manager.list_pdfs())} PDFs stored locally")

    if os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING") is None:
        print("Missing variable AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING in .env")
    else:
        manager = AzureFileManager(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))
        print(f"{len(manager.list_pdfs())} PDFs stored in Azure Blob Storage")