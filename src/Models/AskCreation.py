from sqlalchemy import Integer, String, Boolean, Column, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Etudiant import Etudiant

class AskCreation(db):
  __tablename__ = "AskCreation"
  query: Query

  token = Column(String, primary_key=True)
  mail = Column(String, nullable=False)

  @staticmethod
  def create(token: str, mail: str):
    return AskCreation(token=token, mail=mail)

  def to_json(self):
    return {
      'token': self.token,
      'mail': self.mail
    }
