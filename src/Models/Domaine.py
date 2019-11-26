from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import Query
from server import db

class Domaine(db):
  __tablename__ = "domaine"
  query: Query

  id_domaine = Column(Integer, primary_key=True)
  domaine = Column(String, nullable=False)
  nom = Column(String, nullable=False)

  @staticmethod
  def create(domaine: str, nom: str):
    return Domaine(domaine=domaine, nom=nom)

  def to_json(self):
    return {
      'id': self.id_domaine,
      'domain': self.domaine,
      'name': self.nom
    }
