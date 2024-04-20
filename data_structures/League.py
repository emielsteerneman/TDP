from __future__ import annotations

class League:
    def __init__(self, league_major:str, league_minor:str, league_sub:str = None):
        self.league_major: str = league_major
        self.league_minor: str = league_minor
        self.league_sub: str = league_sub
        
        self.name = f"{self.league_major}_{self.league_minor}"
        if self.league_sub is not None:
            self.name = f"{self.name}_{self.league_sub}"

        self.name_pretty = self.name.replace("_", " ")
        self.name_pretty = " ".join([word.capitalize() for word in self.name_pretty.split(" ")])

        self.name_pretty = self.name_pretty.replace("Smallsize", "SmallSize")
        self.name_pretty = self.name_pretty.replace("Midsize", "MidSize")
        self.name_pretty = self.name_pretty.replace("Standardplatform", "StandardPlatform")
        self.name_pretty = self.name_pretty.replace("Atwork", "@Work")
        self.name_pretty = self.name_pretty.replace("Athome", "@Home")
        self.name_pretty = self.name_pretty.replace("2d", "2D")
        self.name_pretty = self.name_pretty.replace("3d", "3D")

    def to_dict(self) -> dict:
        return {
            "league_major": self.league_major,
            "league_minor": self.league_minor,
            "league_sub": self.league_sub,
            "name": self.name,
            "name_pretty": self.name_pretty
        }

    def to_parts(self)-> list[str]:
        return [ _ for _ in [self.league_major, self.league_minor, self.league_sub] if _ is not None ]

    def __str__(self):
        return self.name_pretty

    def __repr__(self):
        return self.name
    
    @staticmethod
    def from_string(league_str: str) -> League:
        return League(*league_str.split("_"))