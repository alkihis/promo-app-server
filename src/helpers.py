from flask import request, Request
from server import db_session
import os
import datetime
import timestring
from flask_login import current_user
import uuid
import Models.Token

# Allow typing for request object
def get_request() -> Request:
  return request

def get_user():
  return current_user

def is_teacher() -> bool:
  return get_user().teacher

def clean_db():
  from const import DATABASE

  current_date = datetime.date.today()

  try:
    os.rename(DATABASE, DATABASE.replace('.db', '.' + current_date.strftime('%Y-%m-%d') + '.db'))
  except:
    pass
  f = open(DATABASE, "w")
  f.write("")
  f.close()

def convert_datetime(date: str) -> datetime.datetime:
  return timestring.Date(date).date

def create_token_for(id_etu: int, teacher = False):
  ## Crée un token pour l'étudiant
  new_token = str(uuid.uuid4())
  t = Models.Token.Token.create(token=new_token, teacher=teacher, id_etu=id_etu)
  db_session.add(t)
  db_session.commit()

  return t

def convert_date(date: str) -> datetime.date:
  return timestring.Date(date).date.date()

def is_truthy(val: str):
  return val == 'true' or val == '1' or val == 't'
