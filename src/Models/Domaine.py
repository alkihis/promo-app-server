from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship
from server import db

class Domaine(db):
  __tablename__ = "domaine"

  id_domaine = Column(Integer, primary_key=True)
  domaine = Column(String, nullable=False)

  @staticmethod
  def create(domaine: str):
    return Domaine(domaine=domaine)

  def to_json(self):
    return {
      'id': self.id_domaine,
      'domaine': self.domain
    }
