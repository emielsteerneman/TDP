import re

class Semver:
    id_factory = 0
    
    def __init__(self, A=0, B=0, C=0, D=0):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        
        self.id = Semver.id_factory
        Semver.id_factory += 1
    
    @staticmethod
    def parse(version):
        if not Semver.is_semver(version):
            raise ValueError(f"Invalid semver string: {version}")
        values = version.split(".")
        
        # Needed because some papers have a trailing dot after the version number... really why...
        values = [ _ for _ in values if len(_) ] 
        return Semver(*[int(_) for _ in values])

    @staticmethod
    def is_semver(version):
        """Check if a string is in the form of '1.2.3'"""
        return re.match(r"^\d+(\.\d+)*\.?$", version) is not None
    
    def is_followup(self, other):
        if self.A == other.A:
            if self.B == other.B:
                if self.C == other.C:
                    if self.D == other.D:
                        return False
                    else:
                        return self.D > other.C
                else:
                    return self.C > other.C
            else:
                return self.B > other.B
        else:
            return self.A > other.A
        
    def is_strict_followup(self, other):    
        if self.A == other.A:
            if self.B == other.B:
                if self.C == other.C:
                    if self.D == other.D:
                        return False
                    else:
                        return self.D == other.D + 1
                else:
                    return self.C == other.C + 1
            else:
                return self.B == other.B + 1
        else:
            return self.A == other.A + 1

    def is_strictest_followup(self, other):
        if self.A == other.A:
            if self.B == other.B:
                if self.C == other.C:
                    if self.D == other.D:
                        return False
                    else:
                        return self.D == other.D + 1
                else:
                    return self.C == other.C + 1 and self.D == 0
            else:
                return self.B == other.B + 1 and self.C == 0 and self.D == 0
        else:
            return self.A == other.A + 1 and self.B == 0 and self.C == 0 and self.D == 0

    def __repr__(self) -> str:
        semvers = [self.A, self.B, self.C, self.D]
        while 0 < len(semvers) and semvers[-1] == 0: semvers.pop()
        if not len(semvers): semvers = [0] # Happens when semver is 0.0.0.0
        return ".".join([str(_) for _ in semvers])
        # return f"{self.id}|" + ".".join([str(_) for _ in semvers])
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Semver):
            return self.A == __value.A and self.B == __value.B and self.C == __value.C and self.D == __value.D
        else:
            return False
        
    def __hash__(self):
        return self.id
    
class SemverSearch(Semver):
    def __init__(self, A=0, B=0, C=0, D=0, i_sentence=-1, next_needed=False, title=None):
        super().__init__(A, B, C, D)
        
        self.i_sentence = i_sentence
        self.next_needed = next_needed
        self.title=title
    
    @staticmethod
    def from_semver(semver:Semver, i_sentence=-1, next_needed=False, title=None):
        semver_search = SemverSearch(semver.A, semver.B, semver.C, semver.D)
        semver_search.id = semver.id
        semver_search.i_sentence = i_sentence
        semver_search.next_needed = next_needed
        semver_search.title = title
        return semver_search