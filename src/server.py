from flask import Flask
from const import DATABASE
from sqlalchemy import create_engine, Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date
from json import JSONEncoder

##### Define a JSON encoder
""" Module that monkey-patches json module when it's imported so
JSONEncoder.default() automatically checks for a special "to_json()"
method and uses it to encode the object if found.
"""

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder.default  # Save unmodified default.
JSONEncoder.default = _default # Replace it.

##### End JSON encoder

## Create SQL engine
engine = create_engine('sqlite:///' + DATABASE, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
db = declarative_base()
db.query = db_session.query_property()

# Import all the models
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

from login_handler import set_app_login_manager
set_app_login_manager(app)

def init_db():
  db.metadata.create_all(bind=engine)
