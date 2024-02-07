from __future__ import annotations
import numpy as np

class Sentence:
	""" Class that represents a sentence in the database """
	def __init__(self, id:int=None, tdp_id:int=None, paragraph_id:int=None, text_raw:str=None, text_processed:str=None, embedding:np.ndarray=None) -> None:
		self.id = id
		self.tdp_id = tdp_id
		self.paragraph_id = paragraph_id
		self.text_raw = text_raw
		self.text_processed = text_processed
		self.embedding = embedding

	""" Copy all fields from other sentence to this sentence if fields in this sentence are None"""
	def merge(self, other:Sentence) -> None:
		if self.id is None: self.id = other.id
		if self.tdp_id is None: self.tdp_id = other.tdp_id
		if self.paragraph_id is None: self.paragraph_id = other.paragraph_id
		if self.text_raw is None: self.text_raw = other.text_raw
		if self.text_processed is None: self.text = other.text_processed
		if self.embedding is None: self.embedding = other.embedding

	""" Convert sentence to dict """
	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"tdp_id": self.tdp_id,
			"paragraph_id": self.paragraph_id,
			"text_raw": self.text_raw,
			"text_processed": self.text_processed,
			"embedding": self.embedding
		}

	""" Special case of dict that can be converted to json, by removing the np.array embedding """
	def to_json_dict(self) -> str:
		dict_ = self.to_dict()
		dict_.pop("embedding")
		return dict_
 
	@staticmethod
	def from_dict(sentence:dict) -> Sentence:
		return Sentence(
			id=sentence["id"],
			tdp_id=sentence["tdp_id"],
			paragraph_id=sentence["paragraph_id"],
			text_raw=sentence["text_raw"],
			text_processed=sentence["text_processed"],
			embedding=sentence["embedding"]
		)

	def __str__(self) -> str:
		text_raw_short = self.text_raw[:10] + " ... " + self.text_raw[-10:] if len(self.text_raw) > 25 else self.text_raw
		text_processed_short = self.text_processed[:10] + " ... " + self.text_processed[-10:] if len(self.text_processed) > 25 else self.text_processed
		return f"Sentence_db(id={self.id}, tdp_id={self.tdp_id}, paragraph_id={self.paragraph_id}, text='{text_raw_short}', text_raw='{text_processed_short}')"	
  	
	def __dict__(self):
		return self.to_dict()
