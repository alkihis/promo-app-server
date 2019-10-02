from flask import request, Request, g
from sqlite3 import Connection
import os
import sqlite3

__db__ = None

# Allow typing for request object
def getRequest() -> Request:
  return request

DATABASE = './db.db'

def cleanDb():
  os.rename(DATABASE, DATABASE.replace('.db', '.old.db'))
  f = open(DATABASE, "w")
  f.write("")
  f.close()

def getDb() -> Connection:
  try:
    db = getattr(g, '_database', None)
    if db is None:
      db = g._database = sqlite3.connect(DATABASE)
      cursor = db.cursor()
      cursor.execute('PRAGMA foreign_keys = 1;')
    return db
  except:
    return getDbRaw()

def getDbRaw() -> Connection:
  global __db__

  if __db__ is None:
    __db__ = sqlite3.connect(DATABASE)
    cursor = __db__.cursor()
    cursor.execute('PRAGMA foreign_keys = 1;')
  return __db__
