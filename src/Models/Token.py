from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship
from server import db
from Models.Etudiant import Etudiant

class Token(db):
  __tablename__ = "token"

  token = Column(String, primary_key=True)

  type = Column(Boolean, nullable=False)

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu'),
    nullable=True
  )
  etudiant: Etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(token: str, type: int, id_etu: int = None):
    return Token(token=token, type=type, id_etu=id_etu)
