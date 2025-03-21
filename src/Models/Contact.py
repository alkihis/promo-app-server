from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Entreprise import Entreprise

class Contact(db):
  __tablename__ = "contact"
  query: Query

  nom = Column(String, nullable=False)
  id_contact = Column(Integer, primary_key=True)
  mail = Column(String, nullable=False)

  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_entreprise', ondelete='CASCADE'),
    nullable=False
  )
  entreprise: Entreprise = relationship('Entreprise')

  @staticmethod
  def create(nom: str, mail: str, id_entreprise: int):
    return Contact(nom=nom, mail=mail, id_entreprise=id_entreprise)

  def to_json(self, full = False):
    return {
      'id': self.id_contact,
      'name': self.nom,
      'email': self.mail,
      'linked_to': self.id_entreprise if not full else self.entreprise
    }
