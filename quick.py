import fitz
from importlib import reload
from pdf_extraction import extractor as E

d = fitz.open('rtt2023.pdf')

"""

TDP

[sentence]{
	raw text
	factory id
	page number
	paragraph id
}

[paragraph]{
	raw text (which is the title)
	factory id
	page number
	semver
}
[images]{
	
}


debug {
	pagenumbers top
	pagenumbers bottom
	excluded ids?
	image descriptions

}


Do I need to know what (sub)paragraph a sentence belongs to?
- Suggesting entire paragraphs might be easier for RAG
- 

"""