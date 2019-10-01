from flask import request, Request
from sqlite3 import Connection

# Allow typing for request object
def getRequest() -> Request:
  return request

DATABASE = './db.db'

def getDb() -> Connection:
  db = getattr(g, '_database', None)
  if db is None:
      db = g._database = sqlite3.connect(DATABASE)
  return db
