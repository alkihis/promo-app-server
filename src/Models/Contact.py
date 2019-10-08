from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship
from server import db
from Models.Entreprise import Entreprise

class Contact(db):
  __tablename__ = "contact"

  nom = Column(String, nullable=False)
  id_contact = Column(Integer, primary_key=True)
  mail = Column(String, nullable=False)

  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_entreprise'),
    nullable=False
  )
  entreprise: Entreprise = relationship('Entreprise')

  @staticmethod
  def create(nom: str, mail: str, id_entreprise: int):
    return Contact(nom=nom, mail=mail, id_entreprise=id_entreprise)

  def to_json(self):
    return {
      'id': self.id_contact,
      'name': self.nom,
      'email': self.mail,
      'linked_to': self.id_entreprise
    }

