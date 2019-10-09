from flask import request, Request
import os
import datetime
import timestring
from flask_login import current_user

# Allow typing for request object
def get_request() -> Request:
  return request

def get_user():
  return current_user

def is_teacher() -> bool:
  return not get_user().id_etu

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
