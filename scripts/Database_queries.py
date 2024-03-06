from __future__ import annotations
import sqlite3
import io
import numpy as np
import functools

class Database:

	def __init__(self, db_path:str="database_queries.db"):

		self.conn = sqlite3.connect(db_path, check_same_thread=False)
		
		# Create table holding Queries
		self.conn.execute('''
			CREATE TABLE IF NOT EXISTS queries (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               query TEXT NOT NULL,
               date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
        ''')
  
		self.conn.commit()
		print("[DB] Database Queries initialized")
  
	def post_query(self, query:str):
		self.conn.execute('''INSERT INTO queries (query) VALUES (?)''', (query, ))
		self.conn.commit()
		print(f"[DB] Query '{query}' added to database queries")

instance = Database()