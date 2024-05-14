from .Paragraph import Paragraph
from .League import League
from .TeamName import TeamName
from .TDPName import TDPName
from .TDPStructure import TDPStructure

class TDP:
    def __init__(self, tdp_name:TDPName, id: int=None, filehash:str=None, structure:TDPStructure=None):
        self.tdp_name:TDPName = tdp_name
        self.id:int = id
        self.filehash:str = filehash
        self.structure:TDPStructure = structure

    def propagate_information(self):
        # Propagate tdp_name to all paragraphs and sentences
        self.structure.tdp_name = self.tdp_name
        for paragraph in self.structure.paragraphs:
            paragraph.tdp_name = self.tdp_name
            for sentence in paragraph.sentences:
                sentence.tdp_name = self.tdp_name

    def __repr__(self) -> str:
        return f"TDP(team={self.tdp_name.team_name.name_pretty}, year={self.tdp_name.year}, league={self.tdp_name.league.name_pretty})"
    
    def to_dict(self) -> dict:
        return {
            "tdp_name": self.tdp_name.to_dict(),
            "id": self.id,
            "filehash": self.filehash
        }

    def print_outlines(self):
        print("TDP Outline")
        print(f"  Team: {self.tdp_name.team_name}")
        print(f"  Year: {self.tdp_name.year}")
        print(f"  League: {self.tdp_name.league}")
        
        # for paragraph in self.paragraphs:
        #     n_chars = len(paragraph.content_raw())
        #     print(f"    {paragraph.text_raw.ljust(30)}", end="")
        #     print(f" ({len(paragraph.sentences)} sentences, {n_chars} characters, {len(paragraph.images)} images)")

    def print_full(self):
        print("TDP Full")
        print(f"  Team: {self.tdp_name.team_name}")
        print(f"  Year: {self.tdp_name.year}")
        print(f"  League: {self.tdp_name.league}")
        
        # for paragraph in self.paragraphs:
        #     content_raw = paragraph.content_raw()
        #     content_processed = paragraph.content_processed()
        #     n_chars = len(content_raw)
        #     print(f"    {paragraph.text_raw.ljust(30)}", end="")
        #     print(f" ({len(paragraph.sentences)} sentences, {n_chars} characters, {len(paragraph.images)} images)")
        #     print(f"      {content_raw}")
        #     print("\n\n")
            
        print("  End of TDP")

    @staticmethod
    def from_filepath(filepath:str):
        return TDP(TDPName.from_filepath(filepath))