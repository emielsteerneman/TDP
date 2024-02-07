from .Paragraph import Paragraph
from .Sentence import Sentence

class TDP:
    def __init__self(self, id:int=None, filename:str=None, team:str=None, year:int=None, league:str=None, is_etdp:int=None):
        # Information
        self.id:int = id
        self.filename: str = filename
        self.team: str = team
        self.year: int = year
        self.league: str = league
        # Debug information
        self.debug_information = {}
        # Paragraphs
        self.paragraphs: list[Paragraph] = []
        # Sentences
        self.sentences: list[Sentence] = []
        # Images
        self.images = []

    def add_sentence(self, sentence:Sentence):
        self.sentences.append(sentence)
        # Ensure that sentence belongs to an existing paragraph
        if sentence.paragraph_id not in [ _.id for _ in self.paragraphs ]:
            raise ValueError(f"Sentence with id {sentence.id} does not belong to an existing paragraph")
        
    def add_paragraph(self, paragraph:Paragraph):
        self.paragraphs.append(paragraph)