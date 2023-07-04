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
  
	def __str__(self):
		return f"TDP_db(id={self.id}, filename={self.filename}, team={self.team}, year={self.year}, is_etdp={self.is_etdp})"

	def __dict__(self):
		return self.to_dict()

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
  
	def __str__(self) -> str:
		return f"Paragraph_db(id={self.id}, tdp_id={self.tdp_id}, title={self.title})"

	def __dict__(self):
		return self.to_dict()
 
class Sentence_db:
	""" Class that represents a sentence in the database """
	def __init__(self, id:int=None, paragraph_id:int=None, text:str=None, text_raw:str=None, embedding:np.ndarray=None) -> None:
		self.id = id
		self.paragraph_id = paragraph_id
		self.text = text
		self.text_raw = text_raw
		self.embedding = embedding

	""" Copy all fields from other sentence to this sentence if fields in this sentence are None"""
	def merge(self, other:Sentence_db) -> None:
		if self.id is None: self.id = other.id
		if self.paragraph_id is None: self.paragraph_id = other.paragraph_id
		if self.text is None: self.text = other.text
		if self.text_raw is None: self.text_raw = other.text_raw
		if self.embedding is None: self.embedding = other.embedding

	""" Convert sentence to dict """
	def to_dict(self) -> dict:
		return {
			"id": self.id,
			"paragraph_id": self.paragraph_id,
			"text": self.text,
			"text_raw": self.text_raw,
			"embedding": self.embedding
		}

	""" Special case of dict that can be converted to json, by removing the np.array embedding """
	def to_json_dict(self) -> str:
		dict_ = self.to_dict()
		dict_.pop("embedding")
		return dict_
 
	@staticmethod
	def from_dict(sentence:dict) -> Sentence_db:
		return Sentence_db(
			id=sentence["id"],
			paragraph_id=sentence["paragraph_id"],
			text=sentence["text"],
			text_raw=sentence["text_raw"],
			embedding=sentence["embedding"]
		)

	def __str__(self) -> str:
		text_short = self.text[:10] + " ... " + self.text[-10:] if len(self.text) > 25 else self.text
		text_raw_short = self.text_raw[:10] + " ... " + self.text_raw[-10:] if len(self.text_raw) > 25 else self.text_raw
		return f"Sentence_db(id={self.id}, paragraph_id={self.paragraph_id}, text='{text_short}', text_raw='{text_raw_short}')"	
  	
	def __dict__(self):
		return self.to_dict()

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
				text TEXT NOT NULL,
				text_raw TEXT NOT NULL,
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

	def get_tdp_by_rowid(self, rowid:int):
		tdp = self.conn.execute('''SELECT * FROM tdps WHERE rowid = ?''', (rowid,)).fetchone()
		return TDP_db.from_dict(tdp)

	def get_tdp_by_id(self, tdp_id:int):
		tdp = self.conn.execute('''SELECT * FROM tdps WHERE id = ?''', (tdp_id,)).fetchone()
		return TDP_db.from_dict(tdp)
  
	def get_tdp(self, tdp_db:TDP_db):
		tdp = self.conn.execute('''SELECT * FROM tdps WHERE id = ?''', (tdp_db.id,)).fetchone()
		return TDP_db.from_dict(tdp)

	def get_tdps(self):
		tdps = self.conn.execute('''SELECT * FROM tdps''').fetchall()
		return [TDP_db.from_dict(tdp) for tdp in tdps]
  
	def post_tdp(self, tdp_db:TDP_db):
		""" Insert or update a TDP in the database

		Args:
			tdp_db (TDP_db): Instance of the TDP to insert or update. If tdp_db.id is None, insert a new tdp. Otherwise, update the tdp with the same id.

		Raises:
			e: sqlite3.IntegrityError if any constraint except UNIQUE is violated

		Returns:
			TDP_db: Instance of the inserted or updated TDP
		"""
  
		cursor = self.conn.cursor()
		
		# Insert new tdp if id is None
		if tdp_db.id is None:
			# Execute insert query. If UNIQUE constraint is violated, return the existing entry. Otherwise, raise exception.
			try:
				cursor.execute('''INSERT INTO tdps (filename, team, year, is_etdp) VALUES (?, ?, ?, ?)''', 
					(tdp_db.filename, tdp_db.team, tdp_db.year, tdp_db.is_etdp))
				self.conn.commit()
			except sqlite3.IntegrityError as e:
				if "UNIQUE constraint failed" in str(e):
					print(f"[DB] TDP already exists: {tdp_db}")
					# Entry already exists. Return the existing entry
					tdp = self.conn.execute('''SELECT * FROM tdps WHERE team = ? AND year = ? AND is_etdp = ?''', 
						(tdp_db.team, tdp_db.year, tdp_db.is_etdp)).fetchone()
					return TDP_db.from_dict(tdp)
				else:
					print(f"[DB] IntegrityError: {e}")
					raise e
				
		# Update tdp if id is not None
		else:
			# First get the tdp from the database
			tdp_db_old = self.get_tdp(tdp_db)
			# Then merge the old tdp with the new tdp
			tdp_db.merge(tdp_db_old)
			# Execute update query
			cursor.execute('''UPDATE tdps SET filename = ?, team = ?, year = ?, is_etdp = ? WHERE id = ?''', 
				(tdp_db.filename, tdp_db.team, tdp_db.year, tdp_db.is_etdp, tdp_db.id))
			self.conn.commit()

		print(f"[DB] TDP {tdp_db} saved")
		
		# Return an instance of the inserted or updated tdp
		return self.get_tdp_by_rowid(cursor.lastrowid)
	
	def delete_tdp(self, tdp_db:TDP_db):
		# Check if tdp_id is not None
		if tdp_db.id is None:
			raise Exception("[Database][delete_tdp] Missing id")
		
		self.conn.execute('''DELETE FROM tdps WHERE id = ?''', (tdp_db.id,))
		self.conn.commit()
		print(f"[DB] TDP {tdp_db.id} deleted")

	""" Paragraphs """
 
	def get_paragraph_by_rowid(self, rowid:int):
		paragraph = self.conn.execute('''SELECT * FROM paragraphs WHERE rowid = ?''', (rowid,)).fetchone()
		return Paragraph_db.from_dict(paragraph)
 
	def get_paragraph_by_id(self, paragraph_id:int):
		paragraph = self.conn.execute('''SELECT * FROM paragraphs WHERE id = ?''', (paragraph_id,)).fetchone()
		return Paragraph_db.from_dict(paragraph)
 
	def get_paragraph(self, paragraph_db:Paragraph_db):
		return self.get_paragraph_by_id(paragraph_db.id)

	def get_paragraphs(self):
		paragraphs = self.conn.execute('''SELECT * FROM paragraphs''').fetchall()
		return [Paragraph_db.from_dict(paragraph) for paragraph in paragraphs]

	def get_paragraphs_by_tdp(self, tdp_db:TDP_db):
		paragraphs = self.conn.execute('''SELECT * FROM paragraphs WHERE tdp_id = ?''', (tdp_db.id,)).fetchall()
		return [Paragraph_db.from_dict(paragraph) for paragraph in paragraphs]

	def post_paragraph(self, paragraph_db:Paragraph_db):
		cursor = self.conn.cursor()

		# Insert new paragraph if id is None
		if paragraph_db.id is None:
			# Execute insert query. If UNIQUE constraint is violated, return the existing entry. Otherwise, raise exception.
			try:
				cursor.execute('''INSERT INTO paragraphs (tdp_id, title, text, text_raw) VALUES (?, ?, ?, ?)''', 
					(paragraph_db.tdp_id, paragraph_db.title, paragraph_db.text, paragraph_db.text_raw))
				self.conn.commit()
			except sqlite3.IntegrityError as e:
				if "UNIQUE constraint failed" in str(e):
					print(f"[DB] Paragraph already exists: {paragraph_db}")
					# Entry already exists. Return the existing entry
					paragraph = self.conn.execute('''SELECT * FROM paragraphs WHERE tdp_id = ? AND title = ? AND text = ? AND text_raw = ?''',
						(paragraph_db.tdp_id, paragraph_db.title, paragraph_db.text, paragraph_db.text_raw)).fetchone()
					return Paragraph_db.from_dict(paragraph)
				else:
					print(f"[DB] IntegrityError: {e}")
					raise e
     
  		# Update paragraph if id is not None
		else:
			# First get the paragraph from the database
			paragraph_db_old = self.get_paragraph(paragraph_db)
			# Then merge the old paragraph with the new paragraph
			paragraph_db.merge(paragraph_db_old)
			# Execute update query
			cursor.execute('''UPDATE paragraphs SET tdp_id = ?, title = ?, text = ?, text_raw = ? WHERE id = ?''', 
				(paragraph_db.tdp_id, paragraph_db.title, paragraph_db.text, paragraph_db.text_raw, paragraph_db.id))
			self.conn.commit()
   
		print(f"[DB] Paragraph {paragraph_db} saved")

		# Return an instance of the inserted or updated paragraph
		return self.get_paragraph_by_rowid(cursor.lastrowid)
  
	def delete_paragraph(self, paragraph_db:Paragraph_db):
		# Check if paragraph_id is not None
		if paragraph_db.id is None:
			raise Exception("[Database][delete_paragraph] Missing id")
		
		self.conn.execute('''DELETE FROM paragraphs WHERE id = ?''', (paragraph_db.id,))
		self.conn.commit()
		print(f"[DB] Paragraph {paragraph_db.id} deleted")

	""" Sentences """
 
	def get_sentence_by_rowid(self, rowid:int):
		sentence = self.conn.execute('''SELECT * FROM sentences WHERE rowid = ?''', (rowid,)).fetchone()
		return Sentence_db.from_dict(sentence)

	def get_sentence_by_id(self, sentence_id:int):
		sentence = self.conn.execute('''SELECT * FROM sentences WHERE id = ?''', (sentence_id,)).fetchone()
		return Sentence_db.from_dict(sentence)

	def get_sentence(self, sentence_db:Sentence_db):
		return self.get_sentence_by_id(sentence_db.id)

	def get_sentences(self):
		sentences = self.conn.execute('''SELECT * FROM sentences''').fetchall()
		return [Sentence_db.from_dict(sentence) for sentence in sentences]

	def get_sentences_by_paragraph(self, paragraph_db:Paragraph_db=None):
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

	def get_sentence_exhaustive(self, sentence_db:Sentence_db):
		sentence = self.conn.execute('''
			SELECT sentences.*, paragraphs.id AS paragraph_id, paragraphs.title AS paragraph_title, tdps.id AS tdp_id FROM sentences
			INNER JOIN paragraphs ON sentences.paragraph_id = paragraphs.id
			INNER JOIN tdps ON paragraphs.tdp_id = tdps.id
			WHERE sentences.id = ?''', (sentence_db.id,)).fetchone()
		return sentence

	def get_sentences_exhaustive(self):
		sentences = self.conn.execute('''
   			SELECT sentences.*, paragraphs.id AS paragraph_id, tdps.id AS tdp_id FROM sentences
			INNER JOIN paragraphs ON sentences.paragraph_id = paragraphs.id
			INNER JOIN tdps ON paragraphs.tdp_id = tdps.id''').fetchall()
  		
		return sentences
		# return [Sentence_db.from_dict(sentence) for sentence in sentences]	

	def get_sentences_by_tdp(self, tdp_db:TDP_db):
		sentences = self.conn.execute('''SELECT sentences.* FROM sentences
			INNER JOIN paragraphs ON sentences.paragraph_id = paragraphs.id
			INNER JOIN tdps ON paragraphs.tdp_id = tdps.id
			WHERE tdps.id = ?''', (tdp_db.id,)).fetchall()
		return [Sentence_db.from_dict(sentence) for sentence in sentences]

	def post_sentences(self, sentences_db:list[Sentence_db]):
		# First, ensure that all sentences belong to the same paragraph
		paragraph_ids = list(set([sentence_db.paragraph_id for sentence_db in sentences_db]))
		if len(paragraph_ids) != 1: 
			raise Exception("[DB][post_sentences] Not all sentences belong to the same paragraph")

		# Remove all sentences from this paragraph
		self.conn.execute('''DELETE FROM sentences WHERE paragraph_id = ?''', (paragraph_ids[0],))

		# Insert all sentences
		cursor = self.conn.cursor()
		sentence_ids = []
		for sentence_db in sentences_db:
			cursor.execute('''INSERT INTO sentences (paragraph_id, text, text_raw, embedding) VALUES (?, ?, ?, ?)''',
				(sentence_db.paragraph_id, sentence_db.text, sentence_db.text_raw, sentence_db.embedding))
			sentence_ids.append(cursor.lastrowid)
		self.conn.commit()
  
		# Return instances of all inserted sentences
		# TODO: This is not very efficient, but it works for now
		return [self.get_sentence(Sentence_db(id=sentence_id)) for sentence_id in sentence_ids]


instance = Database()