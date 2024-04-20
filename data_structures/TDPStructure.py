class TDPStructure:
    def __init__(self):
        self.sentences = []
        self.paragraphs = []
        self.images = []

    def add_paragraph(self, paragraph):
        self.paragraphs.append(paragraph)

    def get_sentences(self) -> list[str]:
        sentences = []
        for paragraph in self.paragraphs:
            sentences += paragraph.sentences
        return sentences
