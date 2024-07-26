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
from azure.storage.blob import BlobServiceClient, ContentSettings
import dotenv
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
    def store_pdf_from_bytes(self, file_bytes:bytes, tdp_name:TDPName, overwrite:bool=False):
        raise NotImplementedError
    
    @abstractmethod
    def store_html(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False):
        raise NotImplementedError
    
    @abstractmethod
    def store_html_from_bytes(self, file_bytes:bytes, tdp_name:TDPName, overwrite:bool=False):
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
    def get_pdf(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def get_pdf_as_bytes(self, tdp_name:TDPName) -> bytes:
        raise NotImplementedError
    
    @abstractmethod
    def get_html(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def get_html_as_bytes(self, tdp_name:TDPName) -> bytes:
        raise NotImplementedError
    
    """"""""""""""""""""""""""""""""""""""

    

class AzureFileClient(FileClient):

    def __init__(self, connection_string:str):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client("tdps")

    def store_pdf(self, filepath_in:str, tdpname:TDPName, overwrite:bool=False):
        self.store_pdf_from_bytes(open(filepath_in, "rb").read(), tdpname, overwrite)

    def store_pdf_from_bytes(self, file_bytes:bytes, tdp_name:TDPName, overwrite:bool=False):
        content_settings = ContentSettings(content_type="application/pdf", cache_control="max-age=604800")
        name:str = os.path.join(self.PDF_ROOT, tdp_name.to_filepath(TDPName.PDF_EXT))

        self.container_client.upload_blob(name=name, data=file_bytes, content_settings=content_settings)
        logger.info(f"Uploaded {tdp_name} to Azure Blob Storage")

    def store_html(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False):
        self.store_html_from_bytes(open(filepath_in, "rb").read(), tdp_name, overwrite)

    def store_html_from_bytes(self, file_bytes:bytes, tdp_name:TDPName, overwrite:bool=False):
        content_settings = ContentSettings(content_type="text/html", cache_control="max-age=604800")
        name:str = os.path.join(self.HMTL_ROOT, tdp_name.to_filepath(TDPName.HTML_EXT))

        self.container_client.upload_blob(name=name, data=file_bytes, content_settings=content_settings)
        logger.info(f"Uploaded {tdp_name} to Azure Blob Storage")

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

    def delete_pdf(self, tdp_name:TDPName):
        filepath = os.path.join(self.PDF_ROOT, tdp_name.to_filepath(ext=TDPName.PDF_EXT))
        self.container_client.delete_blob(filepath, delete_snapshots="include")

    def delete_html(self, tdp_name:TDPName):
        filepath = os.path.join(self.HMTL_ROOT, tdp_name.to_filepath(ext=TDPName.HTML_EXT))
        self.container_client.delete_blob(filepath, delete_snapshots="include")

    def pdf_exists(self, tdp_name:TDPName):
        raise ValueError("Not implemented")

    def html_exists(self, tdp_name:TDPName):
        raise ValueError("Not implemented")

    def get_filehash(self, tdp_name:TDPName):
        raise ValueError("Not implemented")
    
    def get_pdf(self, tdp_name: TDPName, no_copy: bool = False) -> str:
        raise ValueError("Unsupported operation")

    def get_pdf_as_bytes(self, tdp_name:TDPName) -> bytes:
        filepath = os.path.join(self.PDF_ROOT, tdp_name.to_filepath(TDPName.PDF_EXT))
        try:
            return self.container_client.download_blob(filepath).readall()
        except Exception as e:
            logger.error(f"Failed to download {tdp_name} from Azure Blob Storage at {filepath}")
            raise e

    def get_html(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        raise ValueError("Unsupported operation")
    
    def get_html_as_bytes(self, tdp_name:TDPName) -> bytes:
        filepath = os.path.join(self.HMTL_ROOT, tdp_name.to_filepath(TDPName.HTML_EXT))
        try:
            return self.container_client.download_blob(filepath).readall()
        except Exception as e:
            logger.error(f"Failed to download {tdp_name} from Azure Blob Storage at {filepath}")
            raise e

    
class LocalFileClient(FileClient):
    def __init__(self, root_dir:str):
        if not os.path.isdir(root_dir):
            logger.info(f"Creating directory {root_dir}")
            os.mkdir(root_dir)
        
        self.root_dir:str = root_dir
        self.pdf_root = os.path.join(root_dir, FileClient.PDF_ROOT)
        self.html_root = os.path.join(root_dir, FileClient.HMTL_ROOT)
            
    def store_pdf(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False):
        if self.pdf_exists(tdp_name) and not overwrite:
            raise FileExistsError(f"File {tdp_name} already exists")
        
        filepath_out:str = os.path.join(self.pdf_root, tdp_name.to_filepath(TDPName.PDF_EXT))
        os.makedirs(os.path.dirname(filepath_out), exist_ok=True)
        shutil.copyfile(filepath_in, filepath_out)

    def store_pdf_from_bytes(self, file_bytes:bytes, tdp_name:TDPName, overwrite:bool=False):
        if self.pdf_exists(tdp_name) and not overwrite:
            raise FileExistsError(f"File {tdp_name} already exists")
        
        filepath_out:str = os.path.join(self.pdf_root, tdp_name.to_filepath(TDPName.PDF_EXT))
        os.makedirs(os.path.dirname(filepath_out), exist_ok=True)
        with open(filepath_out, "wb") as f:
            f.write(file_bytes)

    def store_html(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False):
        if self.html_exists(tdp_name) and not overwrite:
            raise FileExistsError(f"File {tdp_name} already exists")
        
        filepath_out:str = os.path.join(self.html_root, tdp_name.to_filepath(TDPName.HTML_EXT))
        os.makedirs(os.path.dirname(filepath_out), exist_ok=True)
        shutil.copyfile(filepath_in, filepath_out)

    def store_html_from_bytes(self, file_bytes:bytes, tdp_name:TDPName, overwrite:bool=False):
        if self.html_exists(tdp_name) and not overwrite:
            raise FileExistsError(f"File {tdp_name} already exists")
        
        filepath_out:str = os.path.join(self.html_root, tdp_name.to_filepath(TDPName.HTML_EXT))
        os.makedirs(os.path.dirname(filepath_out), exist_ok=True)
        with open(filepath_out, "wb") as f:
            f.write(file_bytes)

    def delete_pdf(self, tdp_name:TDPName):
        filepath:str = os.path.join(self.pdf_root, tdp_name.to_filepath())
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File {tdp_name} does not exist")
        os.remove(filepath)

    def delete_html(self, tdp_name:TDPName):
        filepath:str = os.path.join(self.html_root, tdp_name.to_filepath())
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File {tdp_name} does not exist")
        os.remove(filepath)

    def list_pdfs(self) -> tuple[list[TDPName], list[str]]:
        return self.list_files(self.pdf_root, TDPName.PDF_EXT)
    
    def list_htmls(self) -> tuple[list[TDPName], list[str]]:
        return self.list_files(self.html_root, TDPName.HTML_EXT)

    def list_files(self, root, ext) -> tuple[list[TDPName], list[str]]:
        files_listed = []
        for root_, _, files in os.walk(root):
            for file in files:
                if file.endswith(ext):
                    filepath = os.path.join(root_, file)
                    # TODO remove this hack
                    if "misc" in filepath: continue
                    # Remove root_dir from filepath
                    filepath = filepath[len(ext)+1:]
                    files_listed.append(TDPName.from_filepath(filepath))
        hashes = [ self.get_filehash(file, ext) for file in files_listed ]
        return files_listed, hashes

    def pdf_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.pdf_root, tdp_name.to_filepath(ext=TDPName.PDF_EXT))
        return os.path.isfile(filepath)

    def html_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.html_root, tdp_name.to_filepath(ext=TDPName.HTML_EXT))
        return os.path.isfile(filepath)

    def get_filehash(self, tdpname:str|TDPName, ext:str) -> str:
        """Generate md5 base64-encoded hash of a file, equivalent to the hashes in Azure Blob Storage

        Args:
            filepath (str | TDPName): Either the filepath or the TDPName object for the file to hash, relative to the root_dir
            ext (str): The TDPName file extension
            
        Returns:
            str: The md5 base64-encoded hash of the file
        """
        if isinstance(tdpname, TDPName):
            filepath = tdpname.to_filepath(ext)

        root = self.pdf_root if ext == TDPName.PDF_EXT else self.html_root
        rb:bytes = open(os.path.join(root, filepath), "rb").read()
        md5:str = hashlib.md5(rb).digest()
        b64:str = base64.b64encode(md5).decode()
        return b64

    def get_pdf(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        filepath = tdp_name.to_filepath(TDPName.PDF_EXT)

        if no_copy:
            return os.path.join(self.pdf_root, filepath)
        else:
            os.makedirs("tmp", exist_ok=True)
            filepath_tmp = os.path.join("tmp", "temp.pdf")
            shutil.copyfile(os.path.join(self.pdf_root, filepath), filepath_tmp)

            return filepath_tmp

    def get_pdf_as_bytes(self, tdp_name:TDPName) -> bytes:
        filepath = os.path.join(self.pdf_root, tdp_name.to_filepath(TDPName.PDF_EXT))
        return open(filepath, "rb").read()

    def get_html(self, tdp_name:TDPName, no_copy:bool=False) -> str:
        filepath = tdp_name.to_filepath(TDPName.HTML_EXT)

        if no_copy:
            return os.path.join(self.html_root, filepath)
        else:
            os.makedirs("tmp", exist_ok=True)
            filepath_tmp = os.path.join("tmp", "temp.html")
            shutil.copyfile(os.path.join(self.html_root, filepath), filepath_tmp)

            return filepath_tmp

    def get_html_as_bytes(self, tdp_name:TDPName) -> bytes:
        filepath = os.path.join(self.html_root, tdp_name.to_filepath(TDPName.HTML_EXT))
        return open(filepath, "rb").read()

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