from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship
from server import db
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant

class Stage(db):
  __tablename__ = "stage"

  id_stage = Column(Integer, primary_key=True)
  promo = Column(String, nullable=False)
  
  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_entreprise'),
    nullable=False
  )
  entreprise: Entreprise = relationship('Entreprise', back_populates="stages")

  id_domaine = Column(
    Integer,
    ForeignKey('domaine.id_domaine'),
    nullable=False
  )
  domaine: Domaine = relationship('Domaine')

  id_contact = Column(
    Integer,
    ForeignKey('contact.id_contact'),
    nullable=False
  )
  contact: Contact = relationship('Contact')

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu'),
    nullable=False
  )
  etudiant: Etudiant = relationship('Etudiant')

  @staticmethod
  def create(promo: str, id_entreprise: int, id_domaine: int, id_contact: int, id_etu: int):
    return Stage(
      promo=promo, 
      id_entreprise=id_entreprise, 
      id_domaine=id_domaine, 
      id_contact=id_contact,
      id_etu=id_etu
    )

  def to_json(self):
    return {
      'id': self.id_stage,
      'during': self.promo,
      'owner': self.etudiant,
      'company': self.entreprise,
      'referrer': self.contact
    }
  