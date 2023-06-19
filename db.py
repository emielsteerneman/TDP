import sqlite3

class DB:

	def __init__(self):
		self.conn = sqlite3.connect('database.db', check_same_thread=False)
		self.conn.row_factory = sqlite3.Row
		print("[DB] Database opened")

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
		self.conn.commit()
		print("[DB] Table created")
  
	### TDPs ###
  
	def get_tdps(self):
		return self.conn.execute('''
			SELECT * FROM tdps
		''').fetchall()
  
	def get_tdp(self, id):
		return self.conn.execute('''
			SELECT * FROM tdps WHERE id = ?
		''', (id,)).fetchone()
     
  
	def add_tdp(self, filename, team, year, is_etdp):
		print(f"[DB] TDP added: {year} {team}")
		self.conn.execute('''
			INSERT INTO tdps (filename, team, year, is_etdp)
			VALUES (?, ?, ?, ?)
		''', (filename, team, year, is_etdp))
		self.conn.commit()
		# print(f"[DB] TDP added: {year} {team}")