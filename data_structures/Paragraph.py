from __future__ import annotations
import numpy as np
from .Sentence import Sentence
from .Image import Image
from .TDPName import TDPName

class Paragraph:
	""" Class that represents a paragraph in the database """
	def __init__(
     	self, tdp_name:TDPName=None, sequence_id:int=None,
		title_raw:str=None, title_processed:str=None, embedding:np.ndarray=None,
		questions:list[str]=None
  	) -> None:
		self.tdp_name = tdp_name
		self.sequence_id = sequence_id	
		self.title_raw = title_raw
		self.title_processed = title_processed
		self.embedding = embedding
		self.questions = questions
		
		self.sentences:list[Sentence] = []
		self.images:list[Image] = []

	def add_sentence(self, sentence:Sentence):
		sentence.sequence_id = len(self.sentences)
		sentence.paragraph_id = self.sequence_id
		self.sentences.append(sentence)

	def add_sentences(self, sentences:list[Sentence]):
		for sentence in sentences:
			self.add_sentence(sentence)

	def add_image(self, image:Image):
		self.images.append(image)

	def add_images(self, images:list[Image]):
		self.images += images

	def content_raw(self) -> list[str]:
		return " ".join([sentence.text_raw for sentence in self.sentences])

	def content_processed(self) -> list[str]:
		return " ".join([sentence.text_processed for sentence in self.sentences])

	""" Copy all fields from other paragraph to this paragraph if fields in this paragraph are None"""
	def merge(self, other:Paragraph) -> None:
		if self.tdp_name is None: self.tdp_name = other.tdp_name
		if self.sequence_id is None: self.sequence_id = other.sequence_id
		if self.title_raw is None: self.title_raw = other.title_raw
		if self.title_processed is None: self.title_processed = other.title_processed
		if self.embedding is None: self.embedding = other.embedding

	""" Convert paragraph to dict """
	def to_dict(self) -> dict:
		return {
			"sequence_id": self.sequence_id,
			"title_raw": self.title_raw,
			"title_processed": self.title_processed,
			"content_raw": [sentence.text_raw for sentence in self.sentences],
			"content_processed": [sentence.text_processed for sentence in self.sentences],
			"embedding": self.embedding
		}

	""" Special case of dict that can be converted to json, by removing the np.array embedding """
	def to_json_dict(self) -> str:
		dict_ = self.to_dict()
		dict_.pop("embedding")
		return dict_

	@staticmethod
	def from_dict(paragraph:dict) -> Paragraph:
		return Paragraph(
			id=paragraph["id"],
			tdp_name=paragraph["tdp_name"],
			sequence_id=paragraph["sequence_id"],
			title_raw=paragraph["title_raw"],
			title_processed=paragraph["title_processed"],
			embedding=paragraph["embedding"]
		)
  
	# def __str__(self) -> str:
	# 	return f"Paragraph(tdp_name={self.tdp_name}, title={self.text_raw})"

	# def __dict__(self):
	# 	return self.to_dict()