from data_structures.Paragraph import Paragraph
from data_structures.TDPName import TDPName

class ParagraphChunk:
    def __init__(self, paragraph:Paragraph, text:str, sequence_id:int, start:int, end:int):
        self.tdp_name:TDPName =  paragraph.tdp_name
        self.paragraph_sequence_id:int = paragraph.sequence_id
        self.text:str = text
        self.sequence_id:int = sequence_id
        self.start:int = start
        self.end:int = end