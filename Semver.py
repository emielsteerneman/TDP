import re

class Semver:
    def __init__(self, A=0, B=0, C=0, D=0):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
    
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
        """Check if a string is in the form of 'v1.2.3'"""
        return re.match(r"^\d+(\.\d+)*\.?$", version) is not None
    
    def is_followup(self, other):
        if self.A == other.A:
            if self.B == other.B:
                if self.C == other.C:
                    if self.D == other.D:
                        return False
                    else:
                        return self.D < other.C
                else:
                    return self.C < other.C
            else:
                return self.B < other.B
        else:
            return self.A < other.A
        
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
        # Print all values while not null
        semver = f"{self.A}"
        if self.B == 0: return semver
        semver += f".{self.B}"
        if self.C == 0: return semver
        semver += f".{self.C}"
        if self.D == 0: return semver 
        semver += f".{self.D}"
    