from flask import request, Request, g
from sqlite3 import Connection
import os
import sqlite3
import datetime
import timestring

__db__ = None

# Allow typing for request object
def getRequest() -> Request:
  return request

DATABASE = './db.db'

def clean_db():
  current_date = datetime.date.today()

  os.rename(DATABASE, DATABASE.replace('.db', '.' + current_date.strftime('%Y-%m-%d') + '.db'))
  f = open(DATABASE, "w")
  f.write("")
  f.close()


def convert_datetime(date: str) -> datetime.datetime:
  return timestring.Date(date).date


def convert_date(date: str) -> datetime.date:
  return timestring.Date(date).date.date()
