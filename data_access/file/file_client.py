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
    
    # Variables
    PDF_ROOT:str = "pdf"
    HMTL_ROOT:str = "html"

    @abstractmethod
    def store_pdf(filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        raise NotImplementedError

    @abstractmethod
    def list_pdfs(self) -> tuple[list[TDPName, str]]:
        raise NotImplementedError

    @abstractmethod
    def delete_pdf():
        raise NotImplementedError

    @abstractmethod
    def pdf_exists(self, tdp_name:TDPName):
        raise NotImplementedError
    
    @abstractmethod
    def html_exists(self, tdp_name:TDPName):
        raise NotImplementedError

    @abstractmethod
    def get_filehash(self, tdp_name:TDPName):
        raise NotImplementedError

    @abstractmethod
    def get_pdf(self, tdp_name:TDPName, no_copy:bool=False):
        raise NotImplementedError
    
    """"""""""""""""""""""""""""""""""""""

    

class AzureFileClient(FileClient):

    def __init__(self, connection_string:str):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client("tdps")

    def store_pdf(self, filepath_in:str, tdpname:TDPName, overwrite:bool=False):
        file_bytes = open(filepath_in, "rb").read()
        self.container_client.upload_blob(
            name=os.path.join("pdf", tdpname.to_filepath(ext="pdf")),
            data=file_bytes
        )
        logger.info(f"Uploaded {filepath_in} to Azure Blob Storage")

    def store_html(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        file_bytes = open(filepath_in, "rb").read()
        self.container_client.upload_blob(
            name=os.path.join("html", tdp_name.to_filepath(ext="html")),
            data=file_bytes
        )
        logger.info(f"Uploaded {filepath_in} to Azure Blob Storage")

    def list_pdfs(self) -> tuple[list[TDPName], list[str]]:
        return self.list_files(".pdf")

    def list_htmls(self) -> tuple[list[TDPName], list[str]]:
        return self.list_files(".html")

    def list_files(self, ext) -> tuple[list[TDPName], list[str]]:
        files = self.container_client.list_blobs()
        files = [ file for file in files if file.name.endswith(ext) ]
        files = [ file for file in files if "misc" not in file.name ]

        if not len(files):
            return [], []

        afn, ahash = zip(*map(lambda f: [ TDPName.from_filepath(f['name']), base64.b64encode(f['content_settings']['content_md5']).decode('ASCII')], files))

        return afn, ahash

    def delete_pdf():
        raise ValueError("Not implemented")

    def pdf_exists(self, tdp_name:TDPName):
        raise ValueError("Not implemented")

    def html_exists(self, tdp_name:TDPName):
        raise ValueError("Not implemented")

    def get_filehash(self, tdp_name:TDPName):
        raise ValueError("Not implemented")
    
    def get_pdf(self, tdp_name:TDPName, no_copy:bool=False):
        raise ValueError("Not implemented")
    
class LocalFileClient(FileClient):
    def __init__(self, root_dir:str):
        if not os.path.isdir(root_dir):
            logger.info(f"Creating directory {root_dir}")
            os.mkdir(root_dir)
        
        self.root_dir:str = root_dir
        self.pdf_root = os.path.join(root_dir, FileClient.PDF_ROOT)
        self.html_root = os.path.join(root_dir, FileClient.HMTL_ROOT)
            
    def store_pdf(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        if self.pdf_exists(tdp_name) and not (overwrite or increment_index):
            raise FileExistsError(f"File {tdp_name} already exists")
        
        filepath_out:str = os.path.join(self.pdf_root, tdp_name.to_filepath(ext="pdf"))
        os.makedirs(os.path.dirname(filepath_out), exist_ok=True)
        shutil.copyfile(filepath_in, filepath_out)

    def store_html(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        if self.html_exists(tdp_name) and not (overwrite or increment_index):
            raise FileExistsError(f"File {tdp_name} already exists")
        
        filepath_out:str = os.path.join(self.html_root, tdp_name.to_filepath(ext="html"))
        os.makedirs(os.path.dirname(filepath_out), exist_ok=True)
        shutil.copyfile(filepath_in, filepath_out)

    def delete_pdf(self, tdp_name:TDPName):
        filepath:str = os.path.join(self.pdf_root, tdp_name.to_filepath())
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File {tdp_name} does not exist")
        os.remove(filepath)

    def list_pdfs(self) -> tuple[list[TDPName], list[str]]:
        return self.list_files(self.pdf_root, ".pdf")
    
    def list_htmls(self) -> tuple[list[TDPName], list[str]]:
        return self.list_files(self.html_root, ".html")

    def list_files(self, ext_root, ext) -> tuple[list[TDPName], list[str]]:
        files_listed = []
        for root, _, files in os.walk(ext_root):
            for file in files:
                if file.endswith(ext):
                    filepath = os.path.join(root, file)
                    # TODO remove this hack
                    if "misc" in filepath: continue
                    # Remove root_dir from filepath
                    filepath = filepath[len(ext_root)+1:]
                    files_listed.append(TDPName.from_filepath(filepath))
        hashes = [ self.get_filehash(file) for file in files_listed ]
        return files_listed, hashes

    def pdf_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.pdf_root, tdp_name.to_filepath(ext="pdf"))
        return os.path.isfile(filepath)

    def html_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.html_root, tdp_name.to_filepath(ext="html"))
        return os.path.isfile(filepath)

    def get_filehash(self, filepath:str|TDPName) -> str:
        """Generate md5 base64-encoded hash of a file, equivalent to the hashes in Azure Blob Storage

        Args:
            filepath (str | TDPName): Either the filepath or the TDPName object for the file to hash, relative to the root_dir

        Returns:
            str: The md5 base64-encoded hash of the file
        """
        if isinstance(filepath, TDPName):
            filepath = filepath.to_filepath()
    
        rb:bytes = open(os.path.join(self.pdf_root, filepath), "rb").read()
        md5:str = hashlib.md5(rb).digest()
        b64:str = base64.b64encode(md5).decode()
        return b64

    def get_pdf(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        filepath = tdp_name.to_filepath(ext="pdf")

        if no_copy:
            return os.path.join(self.pdf_root, filepath)
        else:
            os.makedirs("tmp", exist_ok=True)
            # Copy file to tmp directory
            filepath_tmp = os.path.join("tmp", "temp.pdf")
            shutil.copyfile(os.path.join(self.pdf_root, filepath), filepath_tmp)

            return filepath_tmp

    def get_html(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        filepath = tdp_name.to_filepath(ext="html")

        if no_copy:
            return os.path.join(self.html_root, filepath)
        else:
            os.makedirs("tmp", exist_ok=True)
            # Copy file to tmp directory
            filepath_tmp = os.path.join("tmp", "temp.html")
            shutil.copyfile(os.path.join(self.html_root, filepath), filepath_tmp)

            return filepath_tmp

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    localmanager = LocalFileClient("static")
    local_pdfs = localmanager.list_pdfs()
    print(f"{len(local_pdfs)} PDFs stored locally")



    azuremanager = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))
    filename = "soccer_smallsize__2025__RoboTeam_Twente__0.pdf"
    tdpname = TDPName.from_filepath(filename)
    azuremanager.store_pdf("soccer_smallsize__2025__RoboTeam_Twente__0.pdf", tdpname)

    # if os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING") is None:
    #     print("Missing variable AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING in .env")
    # else:
    #     azuremanager = AzureFileClient(os.getenv("AZURE_STORAGE_BLOB_TDPS_CONNECTION_STRING"))
    #     print(f"{len(azuremanager.list_pdfs())} PDFs stored in Azure Blob Storage")