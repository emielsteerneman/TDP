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
from Semver import Semver, SemverSearch
from Embeddings import Embeddor as E
from itertools import chain
from typing import List, Tuple, Dict
import functools
import fill_database_tests
import nltk


# nltk.download('stopwords')
from nltk.corpus import stopwords
sw_nltk = stopwords.words('english')


CHARACTER_FILTER = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.,;:!?()[]{}\"'"

tdp_blacklist = ["./TDPs/2022/2022_TDP_Luhbots-Soccer.pdf", "./TDPs/2017/2017_TDP_ULtron.pdf"]
tdp_blacklist.append("./TDPs/2015/2015_ETDP_MRL.pdf") # Blacklist because it's almost a perfect duplicate of their 2016 paper

tdps = U.find_all_TDPs()
tdps = [ _ for _ in tdps if _ not in tdp_blacklist ]

# tdps = [ "./TDPs/2015/2015_TDP_ACES.pdf" ]
# tdps = ["./TDPs/2011/2011_TDP_Cyrus.pdf"] # FalseFalse
# tdps = ["./TDPs/2011/2011_ETDP_Skuba.pdf"] # FalseFalse
# tdps = ["./TDPs/2017/2017_TDP_UBC_Thunderbots.pdf"] # FalseTrue
# tdps = [ _ for _ in tdps if "roboteam" in _.lower() ]
# tdps = ["./TDPs/2014/2014_ETDP_CMDragons.pdf"] # TrueFalse, Very difficult to parse paragraph titles
# tdps = ["./TDPs/2011/2011_TDP_TIGERs_Mannheim.pdf"] # FalseFalse
# tdps = ["./TDPs/2015/2015_ETDP_MRL.pdf"] # FalseFalse Check that names don't end up as paragraph title, after Reference
# tdps = ["./TDPs/2015/2015_TDP_Warthog_Robotics.pdf"]
#"""
n_sentences = 0
total_characters = 0
sentences_all = []

case1 = 0
case2 = 0



def pages_to_sentences(pages, has_page_numbers_top, has_page_numbers_bottom):
    pass


def sentence_to_words(sentence):
    words = sentence.strip().split(" ")
    words = [ word for word in words if len(word) ]
    return words

def resolve_semvers(semvers:List[Semver]):
    # Filter out all semvers that are not strictly followups of one of the previous semvers.
    # For exmaple. given [1, 1.1, 2.0, 9.5, 2.2, 2.4, 3], '9.5' should be dropped since it
    # can not be a followup of '1', '1.1', '2.0'. It wouldn't fit anywhere in a version chain
    semvers_valid = [Semver(0)] # Add this, since it can happen that '1.0.0' occurs multiple times
    for i_semver, semver in enumerate(semvers):
        is_followup = any([ semver.is_strict_followup(semver_prev) for semver_prev in semvers_valid ])
        if is_followup: semvers_valid.append(semver)
    # Remove the first semver, since it is just a bootstrapping semver
    semvers_valid = semvers_valid[1:]
    return resolve_semvers_rec(tuple(semvers_valid))

resolv_i = 0

# Cached recursive function
@functools.cache
def resolve_semvers_rec(semvers:Tuple[Semver], depth=0):
    semvers = list(semvers)
    """ find the longest possible chain of strictly followup semvers """
    global resolv_i
    resolv_i += 1
    
    # Custom print function, to print the depth of the recursion
    p = lambda *args, **kwargs : print(*tuple([f"[rsr][{str(resolv_i).rjust(3)}]{' | '*depth}"] + list(args)), **kwargs)
    # Filter out semvers that are not followups of the given semver
    chain_filter_non_followup = lambda semver, chain: list(filter(lambda s: s.is_followup(semver), chain))
    # Check if any of the semvers in the chain is a strict followup of the given semver
    chain_is_any_strict_followup = lambda semver, chain: any([ semver.is_strict_followup(s) for s in chain ]) or len(chain) == 0
    # Check if chain a is completely within chain b, by looking at the Semver IDs
    chain_a_in_chain_b = lambda chain_a, chain_b: all([ any([a.id == b_.id for b_ in chain_b]) for a in chain_a ])

    if not len(semvers): return []
    
    # p("Got", semvers)
    
    # Grab semver at the front of the chain
    current_semver = semvers.pop(0)

    # Create a list of all possible followup chains
    followup_chains = []
    for i_semver, semver in enumerate(semvers):
        # If this semver is a strict followup of the current semver
        if semver.is_strict_followup(current_semver):
            # Create a new chain, with this semver at the front
            chain = semvers[i_semver:]
            # Filter out all semvers that are not a followup of this semver
            chain = chain_filter_non_followup(current_semver, semvers[i_semver:] )
            # Filter out all semvers that can't fit anywhere in the chain
            chain_ = []
            for i, s in enumerate(chain):
                if chain_is_any_strict_followup(s, chain_):
                    chain_.append(s)
            # Check if this chain is not already completely within another chain            
            chain_present = any([ chain_a_in_chain_b(chain_, chain) for chain in followup_chains ])
            
            if not chain_present: followup_chains.append( chain_ )

    # for chain in followup_chains: p(f"Next: {chain}")

    # Add all followup chains, prepended with the current semver
    # p("Adding followup chains")
    chains = [ [current_semver] + resolve_semvers_rec(tuple(chain), depth+1) for chain in followup_chains ]
    # Add just the current semver as a possible chain
    # p("Adding current semver")
    chains.append( [current_semver] )
    
    # Ignore the current semver, and add all followup chains
    # First, check if this chain is not already within the previous chains
    if not any([ chain_a_in_chain_b(semvers, chain_) for chain_ in chains ]):
        # p("Ignoring current semver")
        chains.append( resolve_semvers_rec(tuple(semvers), depth+1) )
    
    longest_chain = max(chains, key=len, default=[])
    return longest_chain

def find_paragraph_titles(sentences, force_next_needed=None):
    p = lambda *args, **kwargs : print(*tuple(["[fppt]"] + list(args)), **kwargs)
    
    p(f"Finding paragraph titles within {len(sentences)} sentences. (force_next_needed={force_next_needed}))")
    
    semvers = []

    reference_at = -1
    abstract_at = -1
    
    for i_sentence in range(len(sentences)):
        sentence = sentences[i_sentence]
        if sentence.lower().startswith("reference"): 
            reference_at = i_sentence
            break
            
        can_be, next_needed, semver = sentence_can_be_paragraph_title(sentence)
        
        if force_next_needed is not None and force_next_needed != next_needed: continue
                
        # can_be_str = '      '
        # if can_be: can_be_str = 'YES   '
        # if can_be and next_needed: can_be_str = 'YES + '
        # if 50 < len(sentence): p(f"{can_be_str} {i_sentence}".rjust(4), f"{sentence[:24]}...{sentence[-24:]}")
        # else:                  p(f"{can_be_str} {i_sentence}".rjust(4), sentence)
        
        if can_be:
            title = sentence 
            if next_needed:
                title += " " + sentences[i_sentence+1]
            semvers.append(SemverSearch.from_semver(semver, i_sentence, next_needed, title))
        
    start = time.time()
    longest_chain = resolve_semvers(semvers)
    print(f"resolve_semvers took {time.time() - start} seconds")
    print("Longest link:", longest_chain)
    
    return longest_chain
    
    
def sentence_can_be_paragraph_title(sentence_this, sentence_next=None):
    words = sentence_to_words(sentence_this)
    
    # Check if there is a name in the sentence, such as 'Zarghami, M.' or 'Wei, Z.'. 
    # These are not paragraph titles, but probably references
    name_regex = r'([A-Z][a-z]+, [A-Z]\.)'
    if re.search(name_regex, sentence_this): return False, False, None
    
    # If sentence doesn't start with semver, return False
    if not Semver.is_semver(words[0]): return False, False, None
    
    semver = Semver.parse(words[0])
    
    # semvers should be reasonably low. Not something like 1.63.12 or 2015
    if semver.A and semver.A > 20: return False, False, None
    if semver.B and semver.B > 20: return False, False, None
    if semver.C and semver.C > 20: return False, False, None
    if semver.D and semver.D > 20: return False, False, None
    
    # If more than 1 word and last word is not letters, return False
    # if 1 < len(words) and not words[-1].isalpha(): return False, False, None
    
    next_needed = len(words) == 1
    
    return True, next_needed, semver








# Fake sentences of 24 consecutive semvers
# sentences = ["1.0.0", "1.0.1", "1.0.2", "1.1.0", "1.1.1", "1.2.1", "2.0.0", "2.0.1", "2.0.2", "2.1.0", "2.1.1", "2.2.1", "3.0.0", "3.0.1", "3.0.2", "3.1.0", "3.1.1", "3.2.1","4.0.0", "4.0.1", "4.0.2", "4.1.0", "4.1.1", "4.2.1", "."]
# sentences = ["1", "2", "2.1", "2.1.1", "2", "2.1.1.1", "2.1.1.2", "2.1.1.3", "2.1.2", "2.1.2.1", "2.1.3", "2.2", "2.2.1", "2.2.2", "2.2.3", "2.3", "2.4", "2.5", "3", "3", "3.1", "3.1.1", "3.2", "3.3", "3.3.1", "3.3.2", "3.3.3", "4", "4.1", "4.2", "4.3", "4.4", "4.5", "5", "5.1", "."]
# sentences = ["1", "2", "3", "4", "4", "4", "5", "6", "."]
# sentences = ["1", "2", "2", "3", "."]
# find_paragraph_titles(sentences)
# exit()

log_file = open("logfile.txt", "w")



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
        references_found = False
        skipNext = False
        
        has_both_semver_and_title = False
        has_both_semver_and_title_found = False
        
        # Load all pages from the pdf
        pages = [ _.get_text() for _ in list(doc) ]
        # Get all sentences from all pages
        sentences_per_page = [ [line.strip() for line in page.splitlines()] for page in pages ]
        # Remove empty sentences
        sentences_per_page = [ [_ for _ in page if _] for page in sentences_per_page ]
               
        # Check if pdf has page numbers, but only on the odd pages. On even pages, it might go wrong
        # Example of a pdf that goes wrong: 2022_TDP_RoboJackets.pdf page 3: "RoboJackets 2022 Team Description Paper 3"
        has_pagenumbers_top    = all( [ sentences[ 0].strip().isnumeric() for sentences in sentences_per_page[1::2] ] )
        has_pagenumbers_bottom = all( [ sentences[-1].strip().isnumeric() for sentences in sentences_per_page[1::2] ] )
        
        print(f"  Has page numbers top:    {has_pagenumbers_top}")
        print(f"  Has page numbers bottom: {has_pagenumbers_bottom}")
        
        # for i_page, sentences in enumerate(sentences_per_page):
        #     print(i_page, "  ||  ", sentences[0], "  ||  ", sentences[-1])
                
        if has_pagenumbers_top and not has_pagenumbers_bottom:
            # popped = [ sentences.pop(0) for sentences in sentences_per_page[1::] ]
            for i_page in range(1, len(sentences_per_page)):
                while str(i_page+1) != (popped := sentences_per_page[i_page].pop(0)):
                    print("popped", popped)
                print("popped", popped)
            # print("popped:", popped)
        
        if has_pagenumbers_bottom and has_pagenumbers_top:
            [ sentences.pop(-1) for sentences in sentences_per_page[::2] ]
        
        if has_pagenumbers_bottom and not has_pagenumbers_top:
            [ sentences.pop(-1) for sentences in sentences_per_page ]
        
        
        print("\n\n")
        # for i_page, sentences in enumerate(sentences_per_page):
        #     print(i_page, "  ||  ", sentences[0], "  ||  ", sentences[-1])
        
        
        
        # Flatten the list of sentences
        sentences = list(chain.from_iterable( sentences_per_page ))
        
        semver_search_list = find_paragraph_titles(sentences)
        print(f"\nsemver_search_list of length {len(semver_search_list)}")
        for semver_search in semver_search_list:
            i = semver_search.i_sentence
            a = '+' if semver_search.next_needed else '-'
            b = str(i).rjust(5) 
            c = semver_search.title
            d = sentences[i+1] if semver_search.next_needed else ""
            print(f" {a} {b} | {c}")
        
        if len(set([_.next_needed for _ in semver_search_list])) != 1:
            print("Hmm...")
            # Count trues and falses in semver_search_list
            fraction_true = sum([_.next_needed for _ in semver_search_list]) / len(semver_search_list)
            if   fraction_true < 0.3: semver_search_list = find_paragraph_titles(sentences, force_next_needed=False)
            elif 0.7 < fraction_true: semver_search_list = find_paragraph_titles(sentences, force_next_needed=True)
            else:
                log_file.write(f"Can't figure out {tdp}\n")
                print("Can't seem to figure out paragraph titles. Skipping this TDP")
                # exit()
            
                print(f"\nsemver_search_list of length {len(semver_search_list)}")
                for semver_search in semver_search_list:
                    i = semver_search.i_sentence
                    a = '+' if semver_search.next_needed else ' '
                    b = str(i).rjust(5) 
                    c = semver_search.title
                    d = sentences[i+1] if semver_search.next_needed else ""
                    print(f" {a} {b} - {c}")
                    log_file.write(f" {a} {b} - {c}\n")
                print("\n\n\n\n")
                continue

        
        # Split into paragraph titles and sentences

        paragraph_sentences = []
        indices = [0] + [_.i_sentence for _ in semver_search_list] + [len(sentences)]
        for a, b in list(zip(indices, indices[1:])):
            paragraph_sentences.append(sentences[a:b])

        # Drop stuff before introduction, such as title and abstract
        paragraph_sentences.pop(0)

        # For the last paragraph, search for "reference" and drop everything after that
        indices = [i for i, _ in enumerate(paragraph_sentences[-1]) if "reference" in paragraph_sentences[-1][i].lower()]
        if len(indices): paragraph_sentences[-1] = paragraph_sentences[-1][:indices[0]]
       
        paragraph_titles = [ _.title for _ in semver_search_list ]
        
        print(paragraph_titles)
        
        # ==== Test case ==== #
        if tdp in fill_database_tests.test_cases:
            if fill_database_tests.test_cases[tdp] != paragraph_titles:
                raise Exception(f"Test case failed for {tdp}!")
        
                
        for paragraph_title, paragraph in zip(paragraph_titles, paragraph_sentences):
            
            # TODO maybe improve excessive "\n".join() and .splitlines() calls
            text_raw = "\n".join(paragraph)
            text = text_raw

            # print("\n\n")
            # print(text_raw)

            text = text.replace("-\n", "")
            text = text.replace("\n", " ")
            text = text.replace("-", "")

            text = text.replace("Fig.", "Fig ")
            text = text.replace("fig.", "fig.")
            text = text.replace("e.g.", "eg")
            text = text.replace("i.e.", "ie")

            ### Split into sentences
            ## However, don't split on numbers, because those are often part of the sentence
            
            # Find all the indices of the split points
            # Note: Can't use re.split() because it drops the delimiters
            split_indices = np.array([ m.end() for m in re.finditer('[^\d]\.', text) ])
            
            # If there are split points, then there are multiple sentences
            # We need to split the text into multiple sentences
            sentences = []
            if len(split_indices):
                split_indices_norm = [split_indices[0]] + list(np.diff(split_indices))
                for indice in split_indices_norm:
                    sentence, text = text[:indice], text[indice:]
                    sentences.append(sentence)
                    # else:
                    #     print(f"Skipping sentence {len(sentence)} {len(sentence.split(' '))} {    sentence.strip()}")
            else:
                sentences = [ text ]

            # Filter and clean all sentences
            sentences_processed = []
            for sentence in sentences:
                # Filter out sentences that are too short
                if 20 < len(sentence) < 20 or len(sentence.split(" ")) < 3: 
                    sentences_processed.append(None)
                    continue
                
                # Convert to lowercase
                sentence = sentence.lower()
                words = re.findall(r'\w+', sentence)                      # Extract words
                words = [ word for word in words if 1 < len(word)]        # Remove single characters
                words = [ word for word in words if word not in sw_nltk ] # Filter out stopwords
                sentence = " ".join(words)
                sentences_processed.append(sentence)

            text = " ".join(sentences)
                        
            n_sentences += len(sentences)
            total_characters += len(text)

            # Filter out any sentences where sentence_processed is None
            sentences_sentences_processed = list(zip(*[ [s, sp] for s, sp in zip(sentences, sentences_processed) if sp is not None ]))
            if not len(sentences_sentences_processed):
                print("Empty paragraph after filtering sentences")
                continue
            sentences, sentences_processed = sentences_sentences_processed
            
            ### Store everything in the database
            # store paragraph
            paragraph_db = Database.Paragraph_db(tdp_id=tdp_instance.id, title=paragraph_title, text=text, text_raw=text_raw)
            paragraph_db = db_instance.post_paragraph(paragraph_db)

            # Calculate embeddings
            embeddings = [ E.embed(sentence) for sentence in sentences ]
            # embeddings = [ np.zeros(10) for sentence in sentences ]
            
            
            # Store sentences
            sentences_db = [ Database.Sentence_db(text=sentence_processed, text_raw=sentence, embedding=embedding, paragraph_id=paragraph_db.id) for sentence, sentence_processed, embedding in zip(sentences, sentences_processed, embeddings)]
            db_instance.post_sentences(sentences_db)
            

    except Exception as e:
        print(f"Exception on TDP {tdp}: {e}")
        log_file.write(f"Exception on TDP {tdp}: {e}\n\n\n")
        # raise e

print(f"Total sentences: {n_sentences}")
print(f"Total characters: {total_characters}")
    
print(f"Case 1: {case1}")
print(f"Case 2: {case2}")
    
