from __future__ import annotations
import os

from .League import League
from .TeamName import TeamName

class TDPName:

    """ Constructors """

    def __init__(self, league:League, team_name:TeamName, year:int|str, index:int=0) -> TDPName:

        self.league:League = league
        self.team_name:TeamName = team_name
        self.year = int(year)
        self.index = index
    
        self.filename = f"{self.league.name}__{self.year}__{self.team_name.name}__{self.index}" 
    
    @staticmethod
    def from_filepath(filepath:str) -> TDPName:
        filename:str = os.path.basename(filepath)
        filename_no_ext:str = filename.split(".")[0]
        return TDPName.from_string(filename_no_ext)
        
    @staticmethod
    def from_string(string) -> TDPName:
        
        fields = string.split('__')
        
        if len(fields) != 4:
            raise ValueError(f"String '{string}' does not contain 4 fields separated by '__'")
        
        league_str, year, team_str, index = fields
        team_name: TeamName = TeamName(team_str)
        league: League = League.from_string(league_str)
        
        return TDPName (
            league = league,
            year = int(year),
            team_name = team_name,
            index = int(index)
        )

    """ Chainable setters """

    def set_league(self, league:League):
        self.league = league
        return self
    
    def set_team_name(self, team_name:TeamName):
        self.team_name = team_name
        return self
    
    def set_year(self, year:int):
        self.year = year
        return self

    def set_filehash(self, filehash:str):
        self.filehash = filehash
        return self
    
    """ Other """
        
    def to_dict(self) -> dict:
        return {
            "league": self.league.to_dict(),
            "team_name": self.team_name.to_dict(),
            "year": self.year,
            "index": self.index
        }

    def to_filepath(self) -> str:
        return os.path.join(*self.league.to_parts(), str(self.year), self.filename) + ".pdf"

    def __repr__(self):
        return self.filename