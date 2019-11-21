from sqlalchemy import Integer, String, Boolean, Column, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Etudiant import Etudiant

class Token(db):
  __tablename__ = "token"
  query: Query

  token = Column(String, primary_key=True)

  teacher = Column(Boolean, nullable=False)

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu', ondelete="CASCADE"),
    nullable=True
  )
  etudiant: Etudiant = relationship('Etudiant', cascade="all,delete", foreign_keys=[id_etu])

  @staticmethod
  def create(token: str, teacher: bool, id_etu: int = None):
    return Token(token=token, teacher=teacher, id_etu=id_etu)

  def to_json(self):
    return {
      'token': self.token,
      'student': self.etudiant,
      'type': 'teacher' if self.teacher else 'student'
    }
