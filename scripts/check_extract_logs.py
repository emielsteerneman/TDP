# System libraries
import os
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Third party libraries
import matplotlib.pyplot as plt
import numpy as np
# Local libraries
# import startup
# from data_access.file.file_client import LocalFileClient
# from data_structures.TDPName import TDPName
# from data_structures.TDPStructure import TDPStructure
# from extraction import extractor
# from blacklist import blacklist


files = os.listdir("./extract_logs")

nwords_total = []

for f in files[:300]:
    print()
    print(f)
    lines = open(f"./extract_logs/{f}").readlines()
    # print(lines)

    chain_str_me_idx = [ i for i, l in enumerate(lines) if "chain_str_me" in l ][0]
    quality_check_idx = [ i for i, l in enumerate(lines) if "[quality check]" in l ][0]

    chain = lines[chain_str_me_idx+1:quality_check_idx]
    for c in chain: print(c.strip())

    ids_nwords = [ list(map(int, re.findall(r"\d+", c)[:2])) for c in chain ]
    texts = [ c[c.rfind("|")+1:].strip() for c in chain]
    ids, nwords = list(zip(*ids_nwords))

    nwords_diff = np.diff(nwords)
    nwords_total += list(nwords_diff)

    print(ids_nwords)
    print(ids)
    print(texts)

    for n, t in zip(nwords_diff, texts):
        print(f"{n:>4}  {t}")

    if 1000 < np.max(nwords_diff):
        print("???")
        input()

plt.hist(nwords_total, bins=50)
plt.show()