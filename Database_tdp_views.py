from __future__ import annotations
import sqlite3
import io
import numpy as np
import functools
from Database import TDP_db

class Database:

	def __init__(self, db_path:str="database_tdp_views.db"):

		self.conn = sqlite3.connect(db_path, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
		
		# Create table holding TDPs
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS views (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               tdp VARCHAR(255) NOT NULL,
               date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			   ref VARCHAR(255) DEFAULT NULL
			)
        ''')
  
		self.conn.commit()
		print("[DB] Database TDP Views initialized")
  
	def post_tdp(self, tdp_db:TDP_db, ref:str=None):
		entry_string = f"{tdp_db.team} | {tdp_db.year} | {'ETDP' if tdp_db.is_etdp else 'TDP'} | {ref}"
  
		self.conn.execute('''INSERT INTO views (tdp) VALUES (?)''', (entry_string, ))
		self.conn.commit()
		print(f"[DB] TDP {entry_string} added to database tdp views")

		return entry_string

instance = Database()