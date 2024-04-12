from .Paragraph import Paragraph
from .League import League
from .TeamName import TeamName
from .TDPName import TDPName

class TDP:
    def __init__(self, tdp_name:TDPName, id: int=None):
        self.id:int = id
        self.tdp_name:TDPName = tdp_name
        self.paragraphs: list[Paragraph] = []

    def add_paragraph(self, paragraph:Paragraph):
        self.paragraphs.append(paragraph)

    def get_sentences(self) -> list[str]:
        sentences = []
        for paragraph in self.paragraphs:
            sentences += paragraph.sentences
        return sentences

    def __repr__(self) -> str:
        n_sentences = sum([len(paragraph.sentences) for paragraph in self.paragraphs])
        return f"TDP(team={self.tdp_name.team_name.name_pretty}, year={self.tdp_name.year}, league={self.tdp_name.league.name_pretty}, n_paragraphs={len(self.paragraphs)}, n_sentences={n_sentences})"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tdp_name": self.tdp_name.to_dict()
        }

    def print_outlines(self):
        print("TDP Outline")
        print(f"  Team: {self.tdp_name.team_name}")
        print(f"  Year: {self.tdp_name.year}")
        print(f"  League: {self.tdp_name.league}")
        print(f"  Paragraphs: {len(self.paragraphs)}")
        
        for paragraph in self.paragraphs:
            n_chars = len(paragraph.content_raw())
            print(f"    {paragraph.text_raw.ljust(30)}", end="")
            print(f" ({len(paragraph.sentences)} sentences, {n_chars} characters, {len(paragraph.images)} images)")

    def print_full(self):
        print("TDP Full")
        print(f"  Team: {self.tdp_name.team_name}")
        print(f"  Year: {self.tdp_name.year}")
        print(f"  League: {self.tdp_name.league}")
        print(f"  Paragraphs: {len(self.paragraphs)}")
        
        for paragraph in self.paragraphs:
            content_raw = paragraph.content_raw()
            content_processed = paragraph.content_processed()
            n_chars = len(content_raw)
            print(f"    {paragraph.text_raw.ljust(30)}", end="")
            print(f" ({len(paragraph.sentences)} sentences, {n_chars} characters, {len(paragraph.images)} images)")
            print(f"      {content_raw}")
            print("\n\n")
            
        print("  End of TDP")

    @staticmethod
    def from_filepath(filepath:str):
        return TDP(TDPName.from_filepath(filepath))