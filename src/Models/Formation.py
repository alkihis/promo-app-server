from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import Query
from server import db

class Formation(db):
  __tablename__ = "formation"
  query: Query

  id_form = Column(Integer, primary_key=True)
  filiere = Column(String, nullable=False)
  lieu = Column(String, nullable=False)
  niveau = Column(String, nullable=False)

  @staticmethod
  def create(filiere: str, lieu: str, niveau: str):
    return Formation(filiere=filiere, lieu=lieu, niveau=niveau)

  def to_json(self):
    return {
      'id': self.id_form,
      'branch': self.filiere,
      'location': self.lieu,
      'level': self.niveau,
    }

