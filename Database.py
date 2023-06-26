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
  
	def get_tdps(self):
		return self.conn.execute('''
			SELECT * FROM tdps
		''').fetchall()
  
	def get_tdp(self, tdp_id):
		return self.conn.execute('''
			SELECT * FROM tdps WHERE id = ?
		''', (tdp_id,)).fetchone()

	def post_tdp(self, filename, team, year, is_etdp):
		# print(f"[DB] TDP added: {year} {team}")
		cursor = self.conn.cursor()
		cursor.execute('''
			INSERT INTO tdps (filename, team, year, is_etdp)
			VALUES (?, ?, ?, ?)
		''', (filename, team, year, is_etdp))
		self.conn.commit()
		# print(f"[DB] TDP added: {year} {team}")
		return cursor.lastrowid
 
	""" Paragraphs """
 
	def get_paragraph(self, paragraph_id):
		return self.conn.execute('''SELECT * FROM paragraphs WHERE id = ?''', (paragraph_id,)).fetchone()

	def get_paragraphs(self, tdp_id=None):
		if tdp_id is None:
			return self.conn.execute('''SELECT * FROM paragraphs''').fetchall()
		else:
			return self.conn.execute('''SELECT * FROM paragraphs WHERE tdp_id = ?''', (tdp_id,)).fetchall()

	def post_paragraph(self, id, tdp_id, title, text):
		cursor = self.conn.cursor()
		if id == -1:
			cursor.execute('''
				INSERT INTO paragraphs (tdp_id, title, text)
				VALUES (?, ?, ?)
			''', (tdp_id, title, text))
			self.conn.commit()
			# print(f"[DB] Paragraph added to TDP {tdp_id}")
		else:
			cursor.execute('''
				UPDATE paragraphs
				SET title = ?, text = ?
				WHERE id = ?
			''', (title, text, id))
			self.conn.commit()
			print(f"[DB] Paragraph {id} updated")
		return cursor.lastrowid

	def delete_paragraph(self, id):
		self.conn.execute('''
			DELETE FROM paragraphs
			WHERE id = ?
		''', (id,))
		self.conn.commit()
		print(f"[DB] Paragraph {id} deleted")

	""" Sentences """

	def get_sentences(self, paragraph_id=None, inclusive=False):
		# For each sentence, also include team and year through paragraph_id -> tdp_id
		if inclusive:
			return self.conn.execute('''
				SELECT sentences.*, tdps.team, tdps.year FROM sentences
				INNER JOIN paragraphs ON sentences.paragraph_id = paragraphs.id
				INNER JOIN tdps ON paragraphs.tdp_id = tdps.id
			''').fetchall()
		else:
			if paragraph_id is None:
				return self.conn.execute('''
					SELECT * FROM sentences
				''').fetchall()
			else:
				return self.conn.execute('''
					SELECT * FROM sentences WHERE paragraph_id = ?
				''', (paragraph_id,)).fetchall()

	def post_sentences(self, paragraph_id, sentences, embeddings):
		# First, remove all sentences from this paragraph
		self.conn.execute('''DELETE FROM sentences WHERE paragraph_id = ?''', (paragraph_id,))
		# Then, insert each sentence and embedding into the database
		for sentence, embedding in zip(sentences, embeddings):
			self.conn.execute('''
				INSERT INTO sentences (paragraph_id, sentence, embedding)
				VALUES (?, ?, ?)
			''', (paragraph_id, sentence, embedding))
		self.conn.commit()
		# print(f"[DB] {len(sentences)} sentences added to paragraph {paragraph_id}")


instance = Database()