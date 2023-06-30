import utilities as U
import fitz
import re
import numpy as np
import os 
import pickle
from rank_bm25 import BM25Okapi
import time 
import Database
from Database import instance as db_instance
from Semver import Semver
from embeddings import Embeddor as E

CHARACTER_FILTER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.,;:!?()[]{}\"'"

tdp_blacklist = ["./TDPs/2022/2022_TDP_Luhbots-Soccer.pdf", "./TDPs/2017/2017_TDP_ULtron.pdf"]
tdps = U.find_all_TDPs()[:10]
tdps = [ _ for _ in tdps if _ not in tdp_blacklist ]

# tdps = ["./TDPs/2011/2011_TDP_Cyrus.pdf"]
# tdps = ["./TDPs/2011/2011_ETDP_Skuba.pdf"]
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




def pages_to_sentences(pages, has_page_numbers_top, has_page_numbers_bottom):
    pass




for i_tdp, tdp in enumerate(tdps):
    
    print(f"\n\nReading {i_tdp} : {tdp}")
    
    # Add TDP to database
    tdp_instance = U.parse_tdp_name(tdp)
    tdp_instance = db_instance.post_tdp(tdp_instance)
    
    try:
        # Open TDP pdf with PyMuPDF        
        doc = fitz.open(tdp)

        # Create output directory and filename
        _, _, tdp_year, tdp_name = tdp.split("/")
        output_dir = os.path.join("output", tdp_year)
        os.makedirs(output_dir, exist_ok=True)
        output_name = os.path.join(output_dir, f"{tdp_name[:-4]}.txt")
        

        semver_current = Semver()
        paragraph_titles = []
        paragraphs = []
        current_paragraph_title = ""
        current_paragraph = []
        abstract_found = False
        skipNext = False
        
        has_both_semver_and_title = False
        has_both_semver_and_title_found = False
        
        # Load all pages from the pdf
        pages = [ _.get_text() for _ in list(doc) ]
        page_sentences = [ page.splitlines() for page in pages ]
        # Check if pdf has page numbers, but only on the odd pages. On even pages, it might go wrong
        # Example of a pdf that goes wrong: 2022_TDP_RoboJackets.pdf page 3: "RoboJackets 2022 Team Description Paper 3"
        has_pagenumbers_top    = all( [ sentences[ 0].strip().isnumeric() for sentences in page_sentences[1::2] ] )
        has_pagenumbers_bottom = all( [ sentences[-1].strip().isnumeric() for sentences in page_sentences[1::2] ] )

        # print(f"  Has page numbers top:    {has_pagenumbers_top}")
        # print(f"  Has page numbers bottom: {has_pagenumbers_bottom}")

        # For each page, split into paragraph titles and sentences
        # What is a sentence? Something ends with a period. However, take care not to split on 
        # periods in numbers such as 3.1415
        for i_page, sentences in enumerate(page_sentences):
            pagenumber_found = False
            # print(f"\n  Page {i_page} ({len(sentences)} sentences)")

            # For each sentence in page
            for i_sentence, sentence in enumerate(sentences):
                # print(i_sentence, sentence)

                # Skip empty sentences
                if not len(sentence): continue

                # Skip next if needed
                if skipNext:
                    skipNext = False
                    continue
                
                # Skip everything before the abstract. This prevents stuff like "1 Department of ..." from being parsed as a paragraph
                # Example where it goes wrong: 2011_TDP_TIGERs_Mannheim.pdf
                if not abstract_found:
                    abstract_found = "abstract" in sentence.lower()
                    continue
                
                # Split the sentence into words
                words = sentence.strip().split(" ")
                words = [ word for word in words if len(word) ]
                
                # Skip sentences without words
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
                has_correct_formatting = True
                if has_both_semver_and_title_found:
                    if has_both_semver_and_title:
                        has_correct_formatting = issemver and words[-1].isalpha() and 1 < len(words)
                    else:
                        has_correct_formatting = issemver and len(words) == 1
                has_correct_formatting = True

                # New paragraph found?
                if issemver and last_is_word and has_correct_formatting:
                    semver_next = Semver.parse(words[0])
                    # print(f"    {semver_next}")
                    # Check if the next semver is a strict followup of the current semver
                    # Good followups: 1.0.0 -> 1.0.1. 1.1.0. 2.0.0; Bad followups: 1.0.0 -> 1.0.3, 4.1.0, 0.1.0
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
                            has_both_semver_and_title = False
                            case1 += 1
                            # print(f"has_both_semver_and_title set to {has_both_semver_and_title}")
                        else:
                            current_paragraph_title = f"{semver_current} " + " ".join(words[1:])
                            has_both_semver_and_title = True
                            case2 += 1
                            # print(f"has_both_semver_and_title set to {has_both_semver_and_title}")

                        print("-------------------------", current_paragraph_title)
                        has_both_semver_and_title_found = True
                        # print("-"*20, semver_next)
                        
                else:
                    current_paragraph.append(sentence)

        # All pages scanned for paragraph titles and paragraph sentences
        # continue
        
        for paragraph_title, paragraph in zip(paragraph_titles, paragraphs):
            
            

            # TODO maybe improve excessive "\n".join() and .splitlines() calls
            text_raw = ". ".join(paragraph)
            text = "\n".join(paragraph)

            text = text.replace("-\n", "")
            text = text.replace("\n", " ")
            text = text.replace("-", "")

            text = text.replace("Fig.", "Fig ")
            text = text.replace("fig.", "fig.")
            text = text.replace("e.g.", "eg")
            text = text.replace("i.e.", "ie")

            ### Split into sentences
            # However, don't split on numbers, because those are often part of the sentence
            
            # Find all the indices of the split points
            # Note: Can't use re.split() because it drops the delimiters
            split_indices = np.array([ m.end() for m in re.finditer('[^\d]\.', text) ])
            
            # If there are split points, then there are multiple sentences
            # We need to split the text and write each sentence to file
            sentences = []
            if len(split_indices):
                split_indices_norm = [split_indices[0]] + list(np.diff(split_indices))
                for indice in split_indices_norm:
                    sentence, text = text[:indice], text[indice:]
                    if 20 < len(sentence) or 3 < len(sentence.split(" ")):
                        words = re.findall(r'\w+', sentence)                # Extract words
                        words = [ word for word in words if 1 < len(word)]  # Remove single characters
                        sentence = " ".join(words)
                        sentences.append(sentence)
                    else:
                        print(f"Skipping sentence {len(sentence)} {len(sentence.split(' '))} {    sentence.strip()}")
            else:
                sentences = [ text ]

            # Convert to lowercase
            sentences = [ sentence.lower() for sentence in sentences ]

            text = " ".join(sentences)

            paragraph_db = Database.Paragraph_db(tdp_id=tdp_instance.id, title=paragraph_title, text=text, text_raw=text_raw)
            paragraph_db = db_instance.post_paragraph(paragraph_db)

            # Calculate embeddings
            embeddings = [ E.embed(sentence) for sentence in sentences ]
            
            # Store in database
            sentences_db = [ Database.Sentence_db(sentence=sentence, embedding=embedding, paragraph_id=paragraph_db.id) for sentence, embedding in zip(sentences, embeddings)]
            db_instance.post_sentences(sentences_db)
            
            sentences_all += sentences

    except Exception as e:
        print(f"Exception on TDP {tdp}: {e}")
        raise e

print(f"Total sentences: {n_sentences}")
print(f"Total characters: {total_characters}")
    
print(f"Case 1: {case1}")
print(f"Case 2: {case2}")
    
