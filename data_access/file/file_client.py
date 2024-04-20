# System libraries
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from abc import ABC, abstractmethod
import base64
import hashlib
import shutil
# Third party libraries
from azure.storage.blob import BlobServiceClient
# Local libraries
from data_structures.TDPName import TDPName
from MyLogger import logger

class FileClient(ABC):
    
    @abstractmethod
    def store_pdf(filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        raise NotImplementedError

    def list_pdfs(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def delete_pdf():
        raise NotImplementedError

    @abstractmethod
    def pdf_exists(self, tdp_name:TDPName):
        raise NotImplementedError
    
    @abstractmethod
    def get_pdf_hash(self, tdp_name:TDPName):
        raise NotImplementedError

class AzureFileClient(FileClient):

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
        raise ValueError("Not implemented")

    def pdf_exists(self, tdp_name:TDPName):
        raise ValueError("Not implemented")

    def get_pdf_hash(self, tdp_name:TDPName):
        raise ValueError("Not implemented")
    
    def get_pdf(self, tdp_name:TDPName):
        raise ValueError("Not implemented")
    
class LocalFileClient(FileClient):
    def __init__(self, root_dir:str):
        if not os.path.isdir(root_dir):
            logger.info(f"Creating directory {root_dir}")
            os.mkdir(root_dir)
        
        self.root_dir:str = root_dir
            
    def store_pdf(self, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        if self.pdf_exists(tdp_name) and not (overwrite or increment_index):
            raise FileExistsError(f"File {tdp_name} already exists")

    def delete_pdf(self, tdp_name:TDPName):
        filepath:str = os.path.join(self.root_dir, tdp_name.filename)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File {tdp_name} does not exist")
        os.remove(filepath)

    def list_pdfs(self) -> list[TDPName]:
        pdfs = []
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".pdf"):
                    filepath = os.path.join(root, file)
                    # TODO remove this hack
                    if "misc" in filepath: continue
                    # Remove root_dir from filepath
                    filepath = filepath[len(self.root_dir)+1:]
                    pdfs.append(TDPName.from_filepath(filepath))
        return pdfs

    def pdf_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.root_dir, tdp_name.filename)
        return os.path.isfile(filepath)

    def get_pdf_hash(self, filepath:str|TDPName) -> str:
        """Generate md5 base64-encoded hash of a file, equivalent to the hashes in Azure Blob Storage

        Args:
            filepath (str | TDPName): Either the filepath or the TDPName object for the file to hash, relative to the root_dir

        Returns:
            str: The md5 base64-encoded hash of the file
        """
        if isinstance(filepath, TDPName):
            filepath = filepath.to_filepath()
    
        rb:bytes = open(os.path.join(self.root_dir, filepath), "rb").read()
        md5:str = hashlib.md5(rb).digest()
        b64:str = base64.b64encode(md5).decode()
        return b64

    def get_pdf(self, tdp_name:TDPName) -> str:
        filepath = tdp_name.to_filepath()

        os.makedirs("tmp", exist_ok=True)
        # Copy file to tmp directory
        filepath_tmp = os.path.join("tmp", "temp.pdf")
        shutil.copyfile(os.path.join(self.root_dir, filepath), filepath_tmp)

        return filepath_tmp

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    localmanager = LocalFileClient("tdps")
    local_pdfs = localmanager.list_pdfs()
    print(f"{len(local_pdfs)} PDFs stored locally")

    for pdf in local_pdfs:
        if "smallsize" in pdf and "2020" in pdf and "Force" in pdf:
            print(pdf)
            print(localmanager.get_pdf_hash(pdf))

    # if os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING") is None:
    #     print("Missing variable AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING in .env")
    # else:
    #     azuremanager = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))
    #     print(f"{len(azuremanager.list_pdfs())} PDFs stored in Azure Blob Storage")