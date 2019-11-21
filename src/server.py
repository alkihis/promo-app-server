from flask import Flask
from const import DATABASE
from sqlalchemy import create_engine, Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date
from json import JSONEncoder
import os

## File for creating/enabling connection to SQLite database, define ORM models, affect it to Flask app.

##### Define a JSON encoder
""" Module that monkey-patches json module when it's imported so
JSONEncoder.default() automatically checks for a special "to_json()"
method and uses it to encode the object if found.
"""

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder.default  # Save unmodified default.
JSONEncoder.default = _default  # Replace it

##### End JSON encoder

## Create SQL engine
engine = create_engine('sqlite:///' + DATABASE, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
db = declarative_base()
db.query = db_session.query_property()

# Import all the models
# noinspection PyUnresolvedReferences
import Models.Contact
import Models.Etudiant
import Models.Entreprise
import Models.Emploi
import Models.Formation
import Models.Stage
import Models.Token
import Models.Domaine

### Create Flask Server
app = Flask("promo-app-server")

# Database cleaner
def clean_db():
  from const import DATABASE

  current_date = date.today()

  try:
    os.rename(DATABASE, DATABASE.replace('.db', '.' + current_date.strftime('%Y-%m-%d') + '.db'))
  except:
    pass
  f = open(DATABASE, "w")
  f.write("")
  f.close()

def init_db():
  db.metadata.create_all(bind=engine)
