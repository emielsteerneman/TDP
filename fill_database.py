import utilities as U
import fitz
import re
import numpy as np
import os 
import pickle
from rank_bm25 import BM25Okapi
import time 
from Database import instance as db_instance
from Semver import Semver
from embeddings import Embeddor as E

CHARACTER_FILTER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.,;:!?()[]{}\"'"

tdp_blacklist = ["./TDPs/2022/2022_TDP_Luhbots-Soccer.pdf", "./TDPs/2017/2017_TDP_ULtron.pdf"]
tdps = U.find_all_TDPs()[:50]
tdps = [ _ for _ in tdps if _ not in tdp_blacklist ]

# tdps = ["./TDPs/2017/2017_TDP_UBC_Thunderbots.pdf"]
# tdps = [ _ for _ in tdps if "roboteam" in _.lower() ]
# tdps = ["./TDPs/2014/2014_ETDP_CMDragons.pdf"]
# tdps = ["./TDPs/2011/2011_TDP_TIGERs_Mannheim.pdf"]

#"""
n_sentences = 0
total_characters = 0
sentences_all = []

case1 = 0
case2 = 0

for i_tdp, tdp in enumerate(tdps):
    
    print(f"\n\nReading {i_tdp} : {tdp}")
    
    # Add TDP to database
    tdp_instance = U.parse_tdp_name(tdp)
    tdp_id = db_instance.post_tdp(**tdp_instance)
    
    try:
        # Open TDP pdf with PyMuPDF        
        doc = fitz.open(tdp)

        # Create output directory and filename
        _, _, tdp_year, tdp_name = tdp.split("/")
        output_dir = os.path.join("output", tdp_year)
        os.makedirs(output_dir, exist_ok=True)
        output_name = os.path.join(output_dir, f"{tdp_name[:-4]}.txt")
        
        with open(output_name, "w") as output_file:

            semver_current = Semver()
            paragraph_titles = []
            paragraphs = []
            current_paragraph_title = ""
            current_paragraph = []
            abstract_found = False
            skipNext = False
            
            # Load all pages from the pdf
            pages = [ _.get_text().splitlines() for _ in list(doc) ]
            # Check if pdf has page numbers, but only on the odd pages. On even pages, it might go wrong
            # Example of a pdf that goes wrong: 2022_TDP_RoboJackets.pdf page 3: "RoboJackets 2022 Team Description Paper 3"
            has_pagenumbers_top    = all( [ page[ 0].strip().isnumeric() for page in pages[1::2] ] )
            has_pagenumbers_bottom = all( [ page[-1].strip().isnumeric() for page in pages[1::2] ] )

            # print(f"  Has page numbers top:    {has_pagenumbers_top}")
            # print(f"  Has page numbers bottom: {has_pagenumbers_bottom}")

            # For each page, split into paragraph titles and sentences
            # What is a sentence? Something ends with a period. However, take care not to split on 
            # periods in numbers such as 
            for i_page, page in enumerate(doc):
                text = page.get_text()  # TODO get rid of double get_text()? Performance?
                
                # text = re.sub(r' +', ' ', text)
                
                pagenumber_found = False
                
                # print("\n\n\n=====================================")
                # print(f"Page {page.number}")
                # print(repr(text))

                # Find all sentences that start with a number
                sentences = page
                # for i_sentence, sentence in enumerate(sentences): print(f"  Sentence {i_sentence}: |{sentence}|")

                # For each sentence in page
                for i_sentence, sentence in enumerate(sentences):
                    # Skip empty sentences
                    if not len(sentence): continue

                    # Skip next if needed
                    if skipNext:
                        skipNext = False
                        continue
                    
                    # Skip everything before the abstract. This prevents stuff like "1 Department of ..." from being parsed as a paragraph
                    # Example where it goes wrong: 2011_TDP_TIGERs_Mannheim.pdf
                    if not abstract_found:
                        if "abstract" in sentence.lower():
                            abstract_found = True
                        continue
                    
                    # Split the sentence into words
                    words = sentence.strip().split(" ")
                   
                    # Skip empty sentences
                    if not len(words): continue
                    
                    # If the page has page numbers, skip the first and last sentence
                    # 0 < i_page since the first page lacks a pagenumber
                    if 0 < i_page and has_pagenumbers_top and not pagenumber_found:
                        # print(f"Skipping first sentence |{sentence}|")
                        pagenumber_found = str(i_page+1) in words
                        continue
                    if i_sentence == len(sentences)-1 and has_pagenumbers_bottom:
                        # print(f"Skipping last sentence |{sentence}|")
                        continue
                    
                    # If the first word is a semver, and the last word is a word, then it is a paragraph
                    issemver = Semver.is_semver(words[0])
                    last_is_word = len(words) == 1 or words[-1].isalpha()

                    is_paragraph = issemver and last_is_word

                    if is_paragraph:
                        # print(repr(sentences[i_sentence+1]))
                        semver_next = Semver.parse(words[0])
                        if semver_next.is_strict_followup(semver_current):
                            
                            # New paragraph found
                            # First, what to do with the current paragraph?
                            # If we're still in semver 0.*, then it's all title and abstract etc, so we can throw it away
                            # TODO store abstract as well somehow
                            if semver_current.A != 0:
                                # print(f"COMPLETED PARAGRAPH\n  {current_paragraph_title}\n  {current_paragraph[0] if len(current_paragraph) else 'Empty paragraph'}\n")
                            
                                paragraph_titles.append(current_paragraph_title)
                                paragraphs.append(current_paragraph)
                                
                            current_paragraph = []
                            semver_current = semver_next
                            
                            # Get new paragraph title
                            if len(words) == 1:
                                current_paragraph_title = f"{semver_current} " + sentences[i_sentence+1]
                                skipNext = True
                                case1 += 1
                            else:
                                current_paragraph_title = f"{semver_current} " + " ".join(words[1:])
                                case2 += 1
                            
                    else:
                        current_paragraph.append(sentence)

                    # else:
                        # print(f" NO {issemver} {last_is_word} ({words[0]}) |{sentence}|")
                    # print(sentence)


            # for paragraph in paragraphs:
            #     print(paragraph)
            # print("\n\n\n"*2)


            for paragraph_title, paragraph in zip(paragraph_titles, paragraphs):
                # print("\n============================")
                # print("\n")
                # print(paragraph_title)
                # print(paragraph[0])
                # print("\n".join(paragraph))
                
                # TODO maybe improve excessive "\n".join() and .splitlines() calls
                text = "\n".join(paragraph)

                text = text.replace("-\n", "")
                text = text.replace("\n", " ")

                text = text.replace("Fig.", "Fig ")
                text = text.replace("fig.", "fig.")
                text = text.replace("e.g.", "eg")
                text = text.replace("i.e.", "ie")

                # text = re.sub(r'\s+', ' ', text)
                
                paragraph_id = db_instance.post_paragraph(-1, tdp_id, paragraph_title, text)
                
                ### Split into sentences
                # However, don't split on numbers, because those are often part of the sentence
                
                # Find all the indices of the split points
                # Note: Can't use re.split() because it drops the delimiters
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
                    if 20 < len(left) or 3 < len(left.split(" ")):
                        sentences.append(left.strip())
                    else:
                        print(f"Skipping sentence {len(left)} {len(left.split(' '))} {    left.strip()}")
                    text = right

                # Convert to lowercase
                sentences = [ sentence.lower() for sentence in sentences ]
                
                # Calculate embeddings
                embeddings = [ E.embed(sentence) for sentence in sentences ]
                
                # Store in database
                db_instance.post_sentences(paragraph_id, sentences, embeddings)
                
                sentences_all += sentences

                # for sentence in sentences:
                #     print("!!!", sentence)

                # Write everything to file
                for sentence in sentences:
                    # output_file.write(sentence + "\n")
                    n_sentences += 1
                    total_characters += len(sentence)
                    
    except Exception as e:
        print(f"Exception on TDP {tdp}: {e}")

print(f"Total sentences: {n_sentences}")
print(f"Total characters: {total_characters}")
    
print(f"Case 1: {case1}")
print(f"Case 2: {case2}")
    
