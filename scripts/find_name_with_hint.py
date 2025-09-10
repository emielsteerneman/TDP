import re
from difflib import SequenceMatcher

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import startup
from disk_cache import disk_cache

file_client = startup.get_file_client()

@disk_cache()
def get_all_teams():
    print("beep boop")
    filenames, _ = file_client.list_pdfs()
    return list(set([ f.team_name.name_pretty for f in filenames ]))

def _normalize(s: str) -> str:
    # lowercase, collapse non-alphanumerics to single spaces, trim
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def _seq_ratio(a: str, b: str) -> float:
    # 0..1 similarity
    return SequenceMatcher(None, a, b).ratio()

def _token_set_ratio(a: str, b: str) -> float:
    # fuzzywuzzy-style token_set_ratio without dependencies
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    inter = ' '.join(sorted(ta & tb))
    diff  = ' '.join(sorted((ta - tb) | (tb - ta)))
    # compare intersection to unioned strings; favors shared tokens
    if not inter and not diff:
        return 1.0
    return max(
        _seq_ratio(inter, f'{inter} {diff}'.strip()),
        _seq_ratio(f'{inter} {diff}'.strip(), inter)
    )

def _score(hint: str, name: str) -> float:
    nh = _normalize(hint)
    nn = _normalize(name)
    if not nh or not nn:
        return 0.0
    r_char  = _seq_ratio(nh, nn)
    r_token = _token_set_ratio(nh, nn)
    score = max(r_char, r_token)
    # small prefix/substring bonus to punish orthographically-distant junk
    if nn.startswith(nh) or nh.startswith(nn):
        score += 0.05
    elif nh in nn:
        score += 0.03
    return min(score, 1.0)

def find_team_name_using_hint(hint: str, top_k: int = 5, return_scores: bool = True):
    all_teams = get_all_teams()
    ranked = sorted(
        (( _score(hint, team), team) for team in all_teams),
        key=lambda x: x[0],
        reverse=True
    )
    top = ranked[:top_k]
    if return_scores:
        return top  # list of (score, team)
    return [team for _, team in top]
