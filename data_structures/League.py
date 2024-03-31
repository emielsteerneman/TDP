from __future__ import annotations

class League:
    def __init__(self, league_major:str, league_minor:str, league_sub:str = None):
        self.league_major: str = league_major
        self.league_minor: str = league_minor
        self.league_sub: str = league_sub
        
    def __repr__(self):
        league_str = f"{self.league_major}_{self.league_minor}"
        if self.league_sub is not None:
            league_str = f"{league_str}_{self.league_sub}"
        return league_str
    
    @staticmethod
    def from_string(league_str: str) -> League:
        return League(*league_str.split("_"))