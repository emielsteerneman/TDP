from __future__ import annotations
import numpy as np

class Image:
	""" Class that represents an image in the database """
	def __init__(self, id:int=None, filename:str=None, text_raw:str=None, text_processed:str=None, embedding:np.ndarray=None) -> None:
		self.id = id
		self.filename = filename
		self.text_raw = text_raw
		self.text_processed = text_processed
		self.embedding = embedding
		
	""" Copy all fields from other image to this image if fields in this image are None"""
	def merge(self, other:Image) -> None:
		if self.id is None: self.id = other.id
		if self.filename is None: self.filename = other.filename
		if self.text_raw is None: self.text_raw = other.text_raw
		if self.text_processed is None: self.text_processed = other.text_processed
		if self.embedding is None: self.embedding = other.embedding
     
	""" Convert image to dict """
	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"filename": self.filename,
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
	def from_dict(image:dict) -> Image:
		return Image(
			id=image["id"],
			filename=image["filename"],
			text_raw=image["text_raw"],
			text_processed=image["text_processed"],
			embedding=image["embedding"]
		)

	def __str__(self) -> str:
		text_raw_short = self.text_raw[:10] + " ... " + self.text_raw[-10:] if len(self.text_raw) > 25 else self.text_raw
		text_processed_short = self.text_processed[:10] + " ... " + self.text_processed[-10:] if len(self.text_processed) > 25 else self.text_processed
		filename_short = self.filename[:10] + " ... " + self.filename[-10:] if len(self.filename) > 25 else self.filename
		return f"Image_db(id={self.id}, filename={filename_short}, text='{text_raw_short}', text_raw='{text_processed_short}')"

	def __dict__(self):
		return self.to_dict()

