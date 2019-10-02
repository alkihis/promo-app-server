from flask import Flask
from helpers import getDb, cleanDb

def create_db(schema: str):
  db = getDb()

  cur = db.cursor()

  cur.executescript(schema)

  db.commit()

def create():
  cleanDb()
  f = open('src/base.sql', 'r').read()
  create_db(f)