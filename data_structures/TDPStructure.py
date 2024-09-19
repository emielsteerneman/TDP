from .Paragraph import Paragraph
from .Sentence import Sentence
from .TDPName import TDPName

class TDPStructure:
    def __init__(self, tdp_name:TDPName=None):
        self.sentences = []
        self.paragraphs:list[Paragraph] = []
        self.images = []
        self.tdp_name:TDPName = tdp_name

    def add_paragraph(self, paragraph:Paragraph):
        paragraph.sequence_id = len(self.paragraphs)
        self.paragraphs.append(paragraph)

    def get_sentences(self) -> list[Sentence]:
        sentences:list[Sentence] = []
        for paragraph in self.paragraphs:
            sentences += paragraph.sentences
        return sentences

    def outline(self) -> str:
        outline = "TDP outline"
        for paragraph in self.paragraphs:
            outline += f"\n  {paragraph.text_raw}"
        
        return outline