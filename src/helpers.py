from flask import request, Request
from server import db_session
import datetime
import timestring
from flask_login import current_user
import uuid
import Models.Token
import json
from const import SITE_URL

# Allow typing for request object
def get_request() -> Request:
  return request

# Return a User object (defined in login_handler.py)
def get_user():
  return current_user

def is_teacher() -> bool:
  return get_user().teacher

def convert_datetime(date: str) -> datetime.datetime:
  return timestring.Date(date).date

def generate_random_token():
  return str(uuid.uuid4())

def create_token_for(id_etu: int, teacher = False):
  ## Crée un token pour l'étudiant
  new_token = generate_random_token()
  t = Models.Token.Token.create(token=new_token, teacher=teacher, id_etu=id_etu)
  db_session.add(t)
  db_session.commit()

  return t

def generate_login_link_for(id_etu: int):
  token = get_or_create_token_for(id_etu, False)
  return SITE_URL + "/login?token=" + token.token


def get_or_create_token_for(id_etu: int, teacher = False):
  t = Models.Token.Token.query.filter_by(id_etu=id_etu, teacher=teacher).one_or_none()

  if not t:
    t = create_token_for(id_etu, teacher)

  return t


def convert_date(date: str) -> datetime.date:
  if len(date.split('/')) == 3:
    j, m, y = date.split('/')
    return datetime.date(int(y), int(m), int(j))
  
  return timestring.Date(date).date.date()

def is_truthy(val: str):
  return val == 'true' or val == '1' or val == 't'

def get_settings_dict():
  try:
    f = open('settings.json', 'r')
    data = json.load(f)

    return data
  except:
    pass

  return {}

def write_settings_dict(d: dict):
  f = open('settings.json', 'w')
  json.dump(d, f)

def get_teacher_password_hash():
  data = get_settings_dict()

  if 'password' in data:
    return data['password']

  return ""
