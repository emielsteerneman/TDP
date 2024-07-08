class VectorFilter():
    def __init__(self, team:str=None, year_min:int=None, year_max:int=None, year:int=None, league:str=None, leagues:list[str]=None):
        self.team = team
        self.year_min = int(year_min) if year_min is not None else None
        self.year_max = int(year_max) if year_max is not None else None
        self.year = int(year) if year is not None else None
        self.league = league
        self.leagues = leagues

    def from_dict(d:dict):
        team = d.get("team", None)
        year_min = d.get("year_min", None)
        year_max = d.get("year_max", None)
        year = d.get("year", None)
        league = d.get("league", None)
        leagues = d.get("leagues", None)
        if type(leagues) == str: leagues = leagues.split(",")
        return VectorFilter(team=team, year_min=year_min, year_max=year_max, year=year, league=league, leagues=leagues)

    def to_dict(self):
        d = {}
        if self.team is not None: d["team"] = self.team
        if self.year_min is not None: d["year_min"] = self.year_min
        if self.year_max is not None: d["year_max"] = self.year_max
        if self.year is not None: d["year"] = self.year
        if self.league is not None: d["league"] = self.league
        if self.leagues is not None: d["leagues"] = self.leagues
        return d
    
    def __str__(self):
        return str(self.to_dict())