from __future__ import annotations
import sqlite3
import io
import numpy as np

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

""" https://stackoverflow.com/questions/18621513/python-insert-numpy-array-into-sqlite3-database """
def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())

def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)

class TDP_db:
	""" Class that represents a TDP in the database """
	def __init__(self, id:int=None, filename:str=None, team:str=None, year:int=None, is_etdp:int=None) -> None:
		self.id = id
		self.filename = filename
		self.team = team
		self.year = year
		self.is_etdp = is_etdp

	""" Copy all fields from other TDP to this TDP if fields in this TDP are None"""
	def merge(self, other:TDP_db) -> None:
		if self.id is None: self.id = other.id
		if self.filename is None: self.filename = other.filename
		if self.team is None: self.team = other.team
		if self.year is None: self.year = other.year
		if self.is_etdp is None: self.is_etdp = other.is_etdp

	""" Convert TDP to dict """
	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"filename": self.filename,
			"team": self.team,
			"year": self.year,
			"is_etdp": self.is_etdp
		}

	@staticmethod
	def from_dict(tdp:dict) -> TDP_db:
		return TDP_db(
			id=tdp["id"],
			filename=tdp["filename"],
			team=tdp["team"],
			year=tdp["year"],
			is_etdp=tdp["is_etdp"]
		)

class Paragraph_db:
	""" Class that represents a paragraph in the database """
	def __init__(self, id:int=None, tdp_id:int=None, title:str=None, text:str=None, text_raw:str=None) -> None:
		self.id = id
		self.tdp_id = tdp_id
		self.title = title
		self.text = text
		self.text_raw = text_raw

	""" Copy all fields from other paragraph to this paragraph if fields in this paragraph are None"""
	def merge(self, other:Paragraph_db) -> None:
		if self.id is None: self.id = other.id
		if self.tdp_id is None: self.tdp_id = other.tdp_id
		if self.title is None: self.title = other.title
		if self.text is None: self.text = other.text
		if self.text_raw is None: self.text_raw = other.text_raw

	""" Convert paragraph to dict """
	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"tdp_id": self.tdp_id,
			"title": self.title,
			"text": self.text,
			"text_raw": self.text_raw
		}

	@staticmethod
	def from_dict(paragraph:dict) -> Paragraph_db:
		return Paragraph_db(
			id=paragraph["id"],
			tdp_id=paragraph["tdp_id"],
			title=paragraph["title"],
			text=paragraph["text"],
			text_raw=paragraph["text_raw"]
		)

class Sentence_db:
	""" Class that represents a sentence in the database """
	def __init__(self, id:int=None, paragraph_id:int=None, sentence:str=None, embedding:np.ndarray=None) -> None:
		self.id = id
		self.paragraph_id = paragraph_id
		self.sentence = sentence
		self.embedding = embedding

	""" Copy all fields from other sentence to this sentence if fields in this sentence are None"""
	def merge(self, other:Sentence_db) -> None:
		if self.id is None: self.id = other.id
		if self.paragraph_id is None: self.paragraph_id = other.paragraph_id
		if self.sentence is None: self.sentence = other.sentence
		if self.embedding is None: self.embedding = other.embedding

	""" Convert sentence to dict """
	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"paragraph_id": self.paragraph_id,
			"sentence": self.sentence,
			"embedding": self.embedding
		}

	@staticmethod
	def from_dict(sentence:dict) -> Sentence_db:
		return Sentence_db(
			id=sentence["id"],
			paragraph_id=sentence["paragraph_id"],
			sentence=sentence["sentence"],
			embedding=sentence["embedding"]
		)


class Database:

	def __init__(self):

		# Converts np.array to TEXT when inserting
		sqlite3.register_adapter(np.ndarray, adapt_array)
		# Converts TEXT to np.array when selecting
		sqlite3.register_converter("NP_ARRAY", convert_array)

		self.conn = sqlite3.connect('database.db', check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
		self.conn.row_factory = dict_factory
		print("[DB] Database opened")

		# Create tables holding TDPs
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS tdps (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               filename TEXT NOT NULL,
               team TEXT NOT NULL,
               year INTEGER NOT NULL,
               is_etdp INTEGER NOT NULL,
               UNIQUE (team, year, is_etdp)
			)
        ''')
		# Create tables holding paragraphs. Each paragraph belongs to a TDP.
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS paragraphs (
			   id INTEGER PRIMARY KEY AUTOINCREMENT,
			   tdp_id INTEGER NOT NULL,
			   title TEXT NOT NULL DEFAULT '',
			   text TEXT NOT NULL DEFAULT '',
			   text_raw TEXT NOT NULL DEFAULT '',
			   FOREIGN KEY (tdp_id) REFERENCES tdps (id)
			)
		''')

		# Create tables holding sentences. Each sentence belongs to a paragraph. Each sentence has an embedding.
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS sentences (
			   id INTEGER PRIMARY KEY AUTOINCREMENT,
			   paragraph_id INTEGER NOT NULL,
			   sentence TEXT NOT NULL,
			   embedding NP_ARRAY NOT NULL,
			   FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id)
			)
		''')
		# Create database with tags
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS tags (
			   id INTEGER PRIMARY KEY AUTOINCREMENT,
			   tag TEXT NOT NULL UNIQUE,
			   embedding NP_ARRAY NOT NULL
			)
		''')
		# Create database that connects tags and paragraphs
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS tag_paragraph (
			   id INTEGER PRIMARY KEY AUTOINCREMENT,
			   tag_id INTEGER NOT NULL,
			   paragraph_id INTEGER NOT NULL,
			   FOREIGN KEY (tag_id) REFERENCES tags (id),
			   FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id)
			)
		''')
		
		self.conn.commit()
		print("[DB] Table created")
  
	""" TDPs """
  
	def get_tdp_by_id(self, tdp_db:TDP_db):
		tdp = self.conn.execute('''SELECT * FROM tdps WHERE id = ?''', (tdp_db.id,)).fetchone()
		return TDP_db.from_dict(tdp)

	def get_tdps(self):
		tdps = self.conn.execute('''SELECT * FROM tdps''').fetchall()
		return [TDP_db.from_dict(tdp) for tdp in tdps]
  
	def post_tdp(self, tdp_db:TDP_db):
		cursor = self.conn.cursor()
		
		# Insert new tdp if id is None
		if tdp_db.id is None:
			# Check if all the required fields are not None
			if tdp_db.filename is None or tdp_db.team is None or tdp_db.year is None or tdp_db.is_etdp is None:
				raise Exception("[DB][post_tdp] Missing fields")
			# Execute insert query
			cursor.execute('''INSERT INTO tdps (filename, team, year, is_etdp) VALUES (?, ?, ?, ?)''', 
				(tdp_db.filename, tdp_db.team, tdp_db.year, tdp_db.is_etdp))
			self.conn.commit()
		# Update tdp if id is not None
		else:
			# First get the tdp from the database
			tdp_db_old = self.get_tdp_by_id(tdp_db)
			# Then merge the old tdp with the new tdp
			tdp_db.merge(tdp_db_old)
			# Execute update query
			cursor.execute('''
				UPDATE tdps
				SET filename = ?, team = ?, year = ?, is_etdp = ?
				WHERE id = ?
			''', (tdp_db.filename, tdp_db.team, tdp_db.year, tdp_db.is_etdp, tdp_db.id))
			self.conn.commit()

		return cursor.lastrowid
 
	def delete_tdp(self, tdp_db:TDP_db):
		# Check if tdp_id is not None
		if tdp_db.id is None:
			raise Exception("[Database][delete_tdp] Missing id")
		
		self.conn.execute('''DELETE FROM tdps WHERE id = ?''', (tdp_db.id,))
		self.conn.commit()
		print(f"[DB] TDP {tdp_db.id} deleted")

	""" Paragraphs """
 
	def get_paragraph_by_id(self, paragraph_db:Paragraph_db):
		paragraph = self.conn.execute('''SELECT * FROM paragraphs WHERE id = ?''', (paragraph_db.id,)).fetchone()
		return Paragraph_db.from_dict(paragraph)

	def get_paragraphs(self, tdp_id=None):
		if tdp_id is None:
			paragraphs = self.conn.execute('''SELECT * FROM paragraphs''').fetchall()
			return [Paragraph_db.from_dict(paragraph) for paragraph in paragraphs]
		else:
			paragraphs = self.conn.execute('''SELECT * FROM paragraphs WHERE tdp_id = ?''', (tdp_id,)).fetchall()
			return [Paragraph_db.from_dict(paragraph) for paragraph in paragraphs]

	def post_paragraph(self, paragraph_db:Paragraph_db):
		cursor = self.conn.cursor()

		# Insert new paragraph if id is None
		if paragraph_db.id is None:
			# Check if all the required fields are not None
			if paragraph_db.tdp_id is None or paragraph_db.title is None or paragraph_db.text is None or paragraph_db.text_raw is None:
				raise Exception("[DB][post_paragraph] Missing fields")
			# Execute insert query
			cursor.execute('''INSERT INTO paragraphs (tdp_id, title, text, text_raw) VALUES (?, ?, ?, ?)''', 
		  		(paragraph_db.tdp_id, paragraph_db.title, paragraph_db.text, paragraph_db.text_raw))
			self.conn.commit()
		# Update paragraph if id is not None
		else:
			# First get the paragraph from the database
			paragraph_db_old = self.get_paragraph_by_id(paragraph_db)
			# Then merge the old paragraph with the new paragraph
			paragraph_db.merge(paragraph_db_old)
			# Execute update query
			cursor.execute('''
				UPDATE paragraphs
				SET tdp_id = ?, title = ?, text = ?, text_raw = ?
				WHERE id = ?
			''', (paragraph_db.tdp_id, paragraph_db.title, paragraph_db.text, paragraph_db.text_raw, paragraph_db.id))
			self.conn.commit()

		return cursor.lastrowid

	def delete_paragraph(self, paragraph_db:Paragraph_db):
		# Check if paragraph_id is not None
		if paragraph_db.id is None:
			raise Exception("[Database][delete_paragraph] Missing id")
		
		self.conn.execute('''DELETE FROM paragraphs WHERE id = ?''', (paragraph_db.id,))
		self.conn.commit()
		print(f"[DB] Paragraph {paragraph_db.id} deleted")

	""" Sentences """

	def get_sentence_by_id(self, sentence_db:Sentence_db):
		sentence = self.conn.execute('''SELECT * FROM sentences WHERE id = ?''', (sentence_db.id,)).fetchone()
		return Sentence_db.from_dict(sentence)

	def get_sentences(self, paragraph_db:Paragraph_db=None):
		if paragraph_db is None:
			sentences = self.conn.execute('''SELECT * FROM sentences''').fetchall()
			return [Sentence_db.from_dict(sentence) for sentence in sentences]
		else:
			sentences = self.conn.execute('''SELECT * FROM sentences WHERE paragraph_id = ?''', (paragraph_db.id,)).fetchall()
			return [Sentence_db.from_dict(sentence) for sentence in sentences]
		"""
		SELECT sentences.*, tdps.team, tdps.year FROM sentences
		INNER JOIN paragraphs ON sentences.paragraph_id = paragraphs.id
		INNER JOIN tdps ON paragraphs.tdp_id = tdps.id
		"""

	def post_sentences(self, sentences_db:list[Sentence_db]):
		# First, ensure that all sentences belong to the same paragraph
		paragraph_ids = list(set([sentence_db.paragraph_id for sentence_db in sentences_db]))
		if len(paragraph_ids) != 1: 
			raise Exception("[DB][post_sentences] Not all sentences belong to the same paragraph")

		# Remove all sentences from this paragraph
		self.conn.execute('''DELETE FROM sentences WHERE paragraph_id = ?''', (paragraph_ids[0],))

		# Insert all sentences
		for sentence_db in sentences_db:
			self.conn.execute('''INSERT INTO sentences (paragraph_id, sentence, embedding) VALUES (?, ?, ?)''',
				(sentence_db.paragraph_id, sentence_db.sentence, sentence_db.embedding))



instance = Database()