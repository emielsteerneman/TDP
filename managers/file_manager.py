# System libraries
from abc import ABC, abstractmethod
import os

# Local libraries
import utilities as U
from data_structures.TDPName import TDPName

class FileManager(ABC):
    
    @abstractmethod
    def store_pdf(filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        """ Stores a PDF file
        """
        raise NotImplementedError
    
    @abstractmethod
    def delete_pdf():
        raise NotImplementedError

    @abstractmethod
    def pdf_exists(tdp_name:TDPName):
        raise NotImplementedError

class AzureFileManager(FileManager):

    def store_pdf(filepath_in:str, overwrite:bool=False):
        pass
        # azure blob bladibla

class LocalFileManager(FileManager):
    def __init__(self, root_dir:str):
        if not os.path.isdir(root_dir):
            os.mkdir(root_dir)
        
        self.root_dir:str = root_dir
            
    def store_pdf(self, filepath_in:str, tdp_name:TDPName, overwrite:bool=False, increment_index:bool=False):
        if self.pdf_exists(tdp_name) and not (overwrite or increment_index):
            raise FileExistsError(f"File {tdp_name} already exists")
        
    
    def pdf_exists(self, tdp_name: TDPName):
        filepath:str = os.path.join(self.root_dir, tdp_name.filename)
        return os.path.isfile(filepath)