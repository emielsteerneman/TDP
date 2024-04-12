class TeamName:
    def __init__(self, name: str=None, name_pretty: str=None):
        self.name: str = name
        self.name_pretty: str = name_pretty
    
        if self.name is None and self.name_pretty is None:
            raise ValueError("Neither 'name' nor 'name_pretty' was provided")
    
        if self.name is None and self.name_pretty is not None:
            self.name = self.name_pretty.replace(" ", "_")
        
        if self.name is not None and self.name_pretty is None:
            self.name_pretty = self.name.replace("_", " ")

    def to_dict(self):
        return {
            "name": self.name,
            "name_pretty": self.name_pretty
        }

    def __str__(self):
        return self.name_pretty
    
    def __repr__(self):
        return self.name
    
    @staticmethod
    def from_string(name: str):
        return TeamName(name = name.replace(" ", "_"))