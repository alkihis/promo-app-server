from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import Query
from server import db

class Formation(db):
  __tablename__ = "formation"
  query: Query

  id_form = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  lieu = Column(String, nullable=False)

  @staticmethod
  def create(nom: str, lieu: str):
    return Formation(nom=nom, lieu=lieu)

  def to_json(self):
    return {
      'id': self.id_form,
      'name': self.nom,
      'location': self.lieu
    }

