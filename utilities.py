import functools
from typing import List, Tuple, Dict
import os
import shutil
import subprocess
import sys

import Database
from Database import instance as db_instance
from Semver import Semver


def find_all_tdps():
    """Find all TDP pdf files in all subdirectories of current directory"""
    tdps = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pdf") and "TDP" in file:
                tdps.append(os.path.join(root, file))
    return tdps

def find_subset_tdps():
    tdps = find_all_tdps()
    years = [ "2019", "2022", "2023" ]
    teams = [ "tigers", "er-force", "roboteam" ]

    tdps = [ tdp for tdp in tdps if any([ year in tdp for year in years ]) ]
    tdps = [ tdp for tdp in tdps if any([ team in tdp.lower() for team in teams ]) ]

    return tdps

# TDP file name format: <year>_<is_etdp>_<team>.pdf
def parse_tdp_name(filepath):
    """Parse TDP file name and return a dictionary with the fields"""
    filename = os.path.basename(filepath)
    fields = filename.split('.')[0].split('_')
    return Database.TDP_db (
        filename = filename,
        year = fields[0],
        is_etdp = fields[1].lower() == 'etdp',
        team = " ".join(fields[2:])
    )

def find_all_tdps_and_add_to_database(db):
    tdps = find_all_tdps()
    parsed = [parse_tdp_name(tdp) for tdp in tdps]    
    for tdp in parsed:
        db.post_tdp(tdp)
    
def paragraph_to_sentences_embeddings(paragraph):
    sentences = paragraph.split('.')
    embeddings = E.embed(sentences)
    return sentences, embeddings

def resentence_paragraphs():
    print("[resentence_paragraphs] Resentencing paragraphs...")

    # Report total number of sentences
    sentences = db_instance.get_sentences()
    print(f"[resentence_paragraphs] {len(sentences)} sentences found")

    tdps = db_instance.get_tdps()
    print(f"[resentence_paragraphs] {len(tdps)} TDPs found")
    for tdp in tdps:
        print(f"[resentence_paragraphs] Resentencing TDP {tdp['id']} : {tdp['team']} {tdp['year']}")
        paragraphs = db_instance.get_paragraphs(tdp['id'])
        for paragraph in paragraphs:
            print(f"[resentence_paragraphs]     Resentencing paragraph {paragraph['id']} : {paragraph['title']}")
            sentences, embeddings = paragraph_to_sentences_embeddings(paragraph['text'])
            db_instance.post_sentences(paragraph['id'], sentences, embeddings)

    # Report total number of sentences
    sentences = db_instance.get_sentences()
    print(f"[resentence_paragraphs] {len(sentences)} sentences found")

def pdfs_to_html():
    """Convert all TDP pdf files to html files"""
    tdps = db_instance.get_tdps()
    print(tdps[0])
     
    PDFTOHTML_FOLDER_NAME = "pdftohtml_folder"
        
    command = ["pdftohtml", "-c", "-s", "-dataurls"]
    for i_tdp_db, tdp_db in enumerate(tdps):
        try:
            # Create folder
            os.makedirs(PDFTOHTML_FOLDER_NAME, exist_ok=True)
            print(f"Converting {i_tdp_db}/{len(tdps)} {tdp_db.filename}...")
            filepath = f"TDPs/{tdp_db.year}/{tdp_db.filename}"
            shutil.copyfile(filepath, f"{PDFTOHTML_FOLDER_NAME}/{tdp_db.filename}")
            
            subprocess.call(command + [f"{PDFTOHTML_FOLDER_NAME}/{tdp_db.filename}"], stdout=subprocess.DEVNULL)
            
            # wer.pdf is converted to wer-html.html. Copy to static/tdps/id/tdp.html
            filename_html_in = f"{PDFTOHTML_FOLDER_NAME}/{tdp_db.filename.split('.')[0]}-html.html"
            filename_html_out = f"static/tdps/{tdp_db.id}/tdp.html"
            os.makedirs(os.path.dirname(filename_html_out), exist_ok=True)
            shutil.copyfile(filename_html_in, filename_html_out)
        except Exception as e:
            print(f"Error converting {tdp_db.filename}: {e}")
        finally:
            # Clean up folder
            shutil.rmtree(f"{PDFTOHTML_FOLDER_NAME}")


def resolve_semvers(semvers:List[Semver]) -> List[Semver]:
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

# Cached recursive function
@functools.cache
def resolve_semvers_rec(semvers:Tuple[Semver], depth=0):
    semvers = list(semvers)
    """ find the longest possible chain of strictly followup semvers """
    
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

def first_test():
    print("Importing packages...")
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import matplotlib.pyplot as plt

    print("Loading model...")
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    cosine_similarity = lambda a, b: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    paragraph_embeddings = []

    # Get paragraphs from tdp id 63
    paragraphs = db_instance.get_paragraphs(63) + db_instance.get_paragraphs(213)
    for paragraph in paragraphs:
        print(paragraph['title'].rjust(40), "|", paragraph['text'][:100])
        sentences = paragraph['text'].split('.')
        embeddings = model.encode(sentences)
        paragraph_embeddings.append({
            'title': paragraph['title'],
            'embedding_average': np.average(embeddings, axis=0),
            'embeddings': embeddings,
            'sentences': sentences,
            'tdp_id': paragraph['tdp_id']
        })
        

    queries = [
        "I want to know more about ROS and how it works",
        "I want to know more about the wheels",
        "I want to know more about wireless communication between robots",
        "I want to know more about simulation",
        "How does grSim work?",
        "Who created grSim?",
    ]

    for query in queries:

        print()
        print(query)
        query_embedding = model.encode(query)
        
        # Distance between query and average of paragraph embeddings
        distances = [ [cosine_similarity(query_embedding, p['embedding_average']), p] for p in paragraph_embeddings ]
        distances = sorted(distances, reverse=True)
        for distance, p in distances[:5]:
            print(f"{p['tdp_id']}".rjust(5), p['title'].rjust(40), f"{distance:.3f}")

        # Find best matching sentences
        distances_sentences = []
        for p in paragraph_embeddings:
            for sentence, embedding in zip(p['sentences'], p['embeddings']):
                distances_sentences.append([cosine_similarity(query_embedding, embedding), sentence, p])
        distances_sentences = sorted(distances_sentences, key=lambda _: _[0], reverse=True)
        print()
        for distance, sentence, p in distances_sentences[:5]:
            print(f"{p['tdp_id']}".rjust(5), p['title'].rjust(40), f"{distance:.3f}", sentence[:150])

if __name__ == "__main__":
    globals()[sys.argv[1]]()
