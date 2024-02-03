import os
import functools
from typing import List, Tuple, Dict
import numpy as np
import time 

import Database
from Database import instance as db_instance
from Semver import Semver

import matplotlib.pyplot as plt

T_LEN = 100

cosine_similarity = lambda a, b: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# I like this word
def conglomerate(groups):
    print("conglomerate", groups)
    while True:
        print()
        print(groups)
        groups_ = []
        change = False
        ids_found = []
        for i1 in range(len(groups)):
            print(" At group", i1, groups[i1])
            for i2 in range(i1+1, len(groups)):
                overlapping = set(groups[i1]) & set(groups[i2])
                if len(overlapping):
                    union = sorted(list(set(groups[i1]) | set(groups[i2])))
                    print("  overlapping", groups[i1], groups[i2], overlapping, union)
                    if union not in groups_:
                        groups_.append(list(union))
                    change = True
                    ids_found += list(union)
            overlapping = set(groups[i1]) & set(ids_found)
            if not len(overlapping):
                groups_.append(groups[i1])
            # time.sleep(0.15)
        groups = groups_[:]
        if not change: break
    return groups

matches = []

def compare_two_tdps(tdp_id1, tdp_id2):
    
    sentences_1 = db_instance.get_sentences_by_tdp_id(tdp_id1)
    sentences_2 = db_instance.get_sentences_by_tdp_id(tdp_id2)
    
    sentences_1 = [ _ for _ in sentences_1 if T_LEN < len(_['text_raw']) ]
    sentences_2 = [ _ for _ in sentences_2 if T_LEN < len(_['text_raw']) ]

    if not len(sentences_1):
        print(f"No sentences for {tdp_id1} :", db_instance.get_tdp_by_id(tdp_id1))
    if not len(sentences_2):
        print(f"No sentences for {tdp_id2} :", db_instance.get_tdp_by_id(tdp_id2))
    
    counter = 0

    for s1 in sentences_1:
        for s2 in sentences_2:
            sim = cosine_similarity(s1['embedding'], s2['embedding'])
            if 0.80 < sim:
                # print()
                # print(f"{s1['team']} {s1['id']} | {s1['team']} {s2['id']} | {sim}")
                # print(s1['text_raw'])
                # print(s2['text_raw'])

                counter += 1
    
    if counter == 0: return

    f1, f2 = int(100*counter/len(sentences_1)), int(100*counter/len(sentences_2))
    if 50 < f1 or 50 < f2:
        matches.append((tdp_id1, tdp_id2))
        print("\n")
        print(sentences_1[0]['team'], sentences_1[0]['year'], sentences_1[0]['is_etdp'], " | ", sentences_2[0]['team'], sentences_2[0]['year'], sentences_2[0]['is_etdp'])
        print(f"Found {counter} similar sentences out of {len(sentences_1)} ({ f1 }%)  | {len(sentences_2)} ({ f2 }%)")
        print()

tdps = [ _.to_dict() for _ in db_instance.get_tdps() ]
sentences = db_instance.get_sentences_exhaustive()

n_tdps = len(tdps)
max_tdp_id = max([ t['id'] for t in tdps ])

n_sentences = len(sentences)
max_sentence_id = max([ s['id'] for s in sentences ])

print(f"n_sentences: {n_sentences} | max_sentence_id: {max_sentence_id}")

blacklist = [14, 39, 295, 127, 176, 260, 307, 310]

for i in range(1, 334):
    if i in blacklist: continue
    for j in range(i+1, 334):
        print(f"{i} / {j}", end="    \r")
        if j in blacklist: continue
        if i == j: continue
        compare_two_tdps(i, j)

    groups = conglomerate(matches)

    for g in groups:
        print("====")
        for id in g:
            tdp = db_instance.get_tdp_by_id(id)
            print(f"  {tdp.team} {tdp.year} {'ETDP' if tdp.is_etdp else 'TDP'} ")