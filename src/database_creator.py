from flask import Flask
from helpers import getDb

def create_db(schema: str):
  db = getDb()

  db.executemany(schema)
  db.commit()
