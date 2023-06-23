from PyPDF2 import PdfReader
# import utilities as U
import fitz
import re
import numpy as np
import os 
import pickle
from rank_bm25 import BM25Okapi
import time 

def find_all_TDPs():
    """Find all TDP pdf files in all subdirectories of current directory"""
    tdps = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pdf"):
                tdps.append(os.path.join(root, file))
    return tdps

tdps = find_all_TDPs()[:20]
# tdps = [ _ for _ in tdps if "roboteam" in _.lower() ]

# tdps = ["./TDPs/2014/2014_ETDP_CMDragons.pdf"]
# tdps = ["./TDPs/2011/2011_TDP_TIGERs_Mannheim.pdf"]

def is_semver(version):
    """Check if a string is in the form of 'v1.2.3'"""
    return re.match(r"^\d+(\.\d+)*$", version) is not None

def parse_semver(version):
    """Parse a string in the form of 'v1.2.3' into a tuple (1, 2, 3)"""
    return tuple([int(_) for _ in version[1:].split(".")])

class Semver:
    def __init__(self, A=0, B=0, C=0):
        self.A = A
        self.B = B
        self.C = C
    
    @staticmethod
    def parse(version):
        if not is_semver(version):
            raise ValueError(f"Invalid semver string: {version}")
        values = version.split(".")
        return Semver(*[int(_) for _ in values])

    def is_followup(self, other):
        if self.A == other.A:
            if self.B == other.B:
                if self.C == other.C:
                    return False
                else:
                    return self.C < other.C
            else:
                return self.B < other.B
        else:
            return self.A < other.A
        
    def is_strict_followup(self, other):
        if self.A == other.A:
            if self.B == other.B:
                if self.C == other.C:
                    return False
                else:
                    return self.C == other.C + 1
            else:
                return self.B == other.B + 1
        else:
            return self.A == other.A + 1

    def __repr__(self) -> str:
        return f"{self.A}.{self.B}.{self.C}"
    
#"""
n_sentences = 0
total_characters = 0
sentences_all = []

for tdp in tdps:
    # print("\n\n\n*************************************")
    print(f"\n\n\nReading {tdp}")
    doc = fitz.open(tdp)

    # Create output file
    _, _, tdp_year, tdp_name = tdp.split("/")
    output_dir = os.path.join("output", tdp_year)
    os.makedirs(output_dir, exist_ok=True)
    output_name = os.path.join(output_dir, f"{tdp_name[:-4]}.txt")
    
    with open(output_name, "w") as output_file:

        pages = [ _.get_text().splitlines() for _ in list(doc) ]
        
        has_pagenumbers_top    = all( [ page[ 0].isnumeric() for page in pages[1::2] ] )
        has_pagenumbers_bottom = all( [ page[-1].isnumeric() for page in pages[1::2] ] )

        print(has_pagenumbers_top, has_pagenumbers_bottom, tdp)

        semver_current = Semver()
        paragraphs = []
        abstract_found = False

        # if not has_pagenumbers_top and not has_pagenumbers_bottom:
        #     continue

        for i_page, page in enumerate(doc):
            # print("--")
            text = page.get_text()
            text = re.sub(r' +', ' ', text)

            # print("\n\n\n=====================================")
            # print(f"Page {page.number}")
            # print(repr(text))

            # Find all sentences that start with a number
            sentences = text.splitlines()

            for i_sentence, sentence in enumerate(sentences):
                if not len(sentence): continue
                
                if not abstract_found:
                    if "abstract" in sentence.lower():
                        abstract_found = True
                    continue

                words = sentence.strip().split(" ")
                
                if i_sentence == 0 and has_pagenumbers_top:
                    # print(f"Skipping    top pagenumber line |{sentence}|")
                    continue

                if i_sentence == len(sentences)-1 and has_pagenumbers_bottom:
                    # print(f"Skipping bottom pagenumber line |{sentence}|")
                    continue

                if not len(words): continue
                # if not words[0].isdigit(): continue

                issemver = is_semver(words[0])
                last_is_word = len(words) == 1 or words[-1].isalpha()

                is_paragraph = issemver and last_is_word

                if is_paragraph:
                    # print(f"YES ({words[0]}) |{sentence}|")
                    # print(repr(sentences[i_sentence+1]))
                    semver_next = Semver.parse(words[0])
                    if semver_next.is_strict_followup(semver_current):
                        # print(f"{semver_current} -> {semver_next}")
                        semver_current = semver_next

                        if len(words) == 1:
                            paragraphs.append( F"{semver_current} " + sentences[i_sentence+1] )
                        else:
                            paragraphs.append( F"{semver_current} " + " ".join(words[1:]) )

                # else:
                    # print(f" NO {issemver} {last_is_word} ({words[0]}) |{sentence}|")
                # print(sentence)

        for paragraph in paragraphs:
            print(paragraph)
        print("\n\n\n"*2)

        continue

        """
            text = text.replace("-\n", "")
            text = text.replace("\n", " ")

            text = text.replace("Fig.", "Fig ")
            text = text.replace("fig.", "fig.")
            text = text.replace("e.g.", "eg")
            text = text.replace("i.e.", "ie")

            text = re.sub(r'\s+', ' ', text)
            
            # Find all the indices of the split points
            split_indices = np.array([ m.end() for m in re.finditer('[^\d]\.', text) ])
            
            # If there is just one sentence, then there will be no split points
            # If that happens, simply write to file and continue
            if len(split_indices) == 0:
                output_file.write(text)
                continue

            # If there are split points, then there are multiple sentences
            # We need to split the text and write each sentence to file
            split_indices_norm = [split_indices[0]] + list(np.diff(split_indices))
            sentences = []
            for indice in split_indices_norm:
                left, right = text[:indice], text[indice:]
                sentences.append(left.strip())
                text = right

            sentences_all += sentences

            # Write everything to file
            for sentence in sentences:
                output_file.write(sentence + "\n")
                n_sentences += 1
                total_characters += len(sentence)
        """

print(f"Total sentences: {n_sentences}")
print(f"Total characters: {total_characters}")
    
# Write all sentences to a pickle file
# with open("sentences_all.pkl", "wb") as f:
#     pickle.dump(sentences_all, f)
#"""

"""
# Load all sentences from pickle file
sentences_all = None
now = time.time()
with open("sentences_all.pkl", "rb") as f:
    sentences_all = pickle.load(f)
print(f"Time taken to load pickle file: {time.time() - now:.2f} seconds")

now = time.time()
tokenized_corpus = [doc.split(" ") for doc in sentences_all]
bm25 = BM25Okapi(tokenized_corpus)
print(f"Time taken to create BM25 model: {time.time() - now:.2f} seconds")

query = "What does grsim do?"
tokenized_query = query.split(" ")

now = time.time()
doc_scores = bm25.get_scores(tokenized_query)
print(f"Time taken to get scores: {time.time() - now:.2f} seconds")
for score in doc_scores:
    print(score)

argsort = np.argsort(doc_scores)[::-1]
for i in range(5):
    print(sentences_all[argsort[i]])

# now = time.time()
# topk = bm25.get_top_n(tokenized_query, tokenized_corpus, n=5)
# print(f"Time taken to get scores: {time.time() - now:.2f} seconds")
# print(topk)
"""