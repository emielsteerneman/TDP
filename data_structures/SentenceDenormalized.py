from __future__ import annotations
from .League import League
import numpy as np

class SentenceDenormalized:
    def __init__(
        self, id:int=None, tdp_id:int=None, paragraph_id:int=None, sequence_id:int=None,
        text_raw:str=None, text_processed:str=None, embedding:np.ndarray=None,
        team:str=None, year:int=None, league:League=None
    ) -> None:
        self.id: int = id
        self.tdp_id: int = tdp_id
        self.paragraph_id: int = paragraph_id
        self.sequence_id: int = sequence_id
        self.text_raw: str = text_raw
        self.text_processed: str = text_processed
        self.embedding: np.ndarray = embedding
        self.team: str = team
        self.year: int = year
        self.league: League = league    

    """ Convert sentence to dict """
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tdp_id": self.tdp_id,
            "paragraph_id": self.paragraph_id,
            "sequence_id": self.sequence_id,
            "text_raw": self.text_raw,
            "text_processed": self.text_processed,
            "embedding": self.embedding,
            "team": self.team,
            "year": self.year,
            "league": self.league
        }


    """ Special case of dict that can be converted to json, by removing the np.array embedding """
    def to_json_dict(self) -> str:
        dict_ = self.to_dict()
        dict_.pop("embedding")
        return dict_

    @staticmethod
    def from_dict(sentence:dict) -> SentenceDenormalized:
        return SentenceDenormalized(
            id=sentence["id"],
            tdp_id=sentence["tdp_id"],
            paragraph_id=sentence["paragraph_id"],
            sequence_id=sentence["sequence_id"],
            text_raw=sentence["text_raw"],
            text_processed=sentence["text_processed"],
            embedding=sentence["embedding"],
            team=sentence["team"],
            year=sentence["year"],
            league=sentence["league"]
        )
