from sqlalchemy import Integer, String, Boolean, Column, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Etudiant import Etudiant

class Token(db):
  __tablename__ = "token"
  query: Query

  token = Column(String, primary_key=True)

  type = Column(Boolean, nullable=False)

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu'),
    nullable=True
  )
  etudiant: Etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(token: str, type: bool, id_etu: int = None):
    return Token(token=token, type=type, id_etu=id_etu)
