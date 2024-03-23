from .Paragraph import Paragraph
from .SentenceDenormalized import SentenceDenormalized

class TDP:
    def __init__(self, id:int=None, filename:str=None, team:str=None, year:int=None, league:str=None, is_etdp:int=None):
        self.id:int = id
        self.filename: str = filename
        self.team: str = team
        self.year: int = year
        self.league: str = league
        self.paragraphs: list[Paragraph] = []

        if self.year is not None:
            self.year = int(self.year)

    def denormalize(self):
        sentences_denormalized_all = []
        for i_paragraph, paragraph in enumerate(self.paragraphs):
            for sentence in paragraph.sentences:
                sentence_denormalized = SentenceDenormalized(
                    **sentence.to_dict(),
                    tdp_id = self.id,
                    team = self.team,
                    year = self.year,
                    league = self.league,                    
                    paragraph_id = paragraph.id,
                )
                sentences_denormalized_all.append(sentence_denormalized)
        return sentences_denormalized_all   

    def add_paragraph(self, paragraph:Paragraph):
        self.paragraphs.append(paragraph)

    def get_sentences(self) -> list[str]:
        sentences = []
        for paragraph in self.paragraphs:
            sentences += paragraph.sentences
        return sentences

    def __repr__(self) -> str:
        n_sentences = sum([len(paragraph.sentences) for paragraph in self.paragraphs])
        return f"TDP(team={self.team}, year={self.year}, league={self.league}, n_paragraphs={len(self.paragraphs)}, n_sentences={n_sentences})"
    
    def print_outlines(self):
        print("TDP Outline")
        print(f"  Team: {self.team}")
        print(f"  Year: {self.year}")
        print(f"  League: {self.league}")
        print(f"  Paragraphs: {len(self.paragraphs)}")
        
        for paragraph in self.paragraphs:
            n_chars = len(paragraph.content_raw())
            print(f"    {paragraph.text_raw.ljust(30)}", end="")
            print(f" ({len(paragraph.sentences)} sentences, {n_chars} characters, {len(paragraph.images)} images)")

    def print_full(self):
        print("TDP Full")
        print(f"  Team: {self.team}")
        print(f"  Year: {self.year}")
        print(f"  League: {self.league}")
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