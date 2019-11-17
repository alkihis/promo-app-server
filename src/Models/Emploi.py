from sqlalchemy import Integer, String, Column, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant
from datetime import date

class Emploi(db):
  __tablename__ = "emploi"
  query: Query

  id_emploi = Column(Integer, primary_key=True)
  debut = Column(Date, nullable=False)
  fin = Column(Date)
  contrat = Column(String, nullable=False)
  salaire = Column(Integer)
  niveau = Column(String, nullable=False)
  
  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_entreprise', ondelete='SET NULL'),
    nullable=False
  )
  entreprise: Entreprise = relationship('Entreprise', back_populates="emplois")

  id_domaine = Column(
    Integer,
    ForeignKey('domaine.id_domaine', ondelete='SET NULL'),
    nullable=False
  )
  domaine: Domaine = relationship('Domaine', foreign_keys=[id_domaine])

  id_contact = Column(
    Integer,
    ForeignKey('contact.id_contact', ondelete='SET NULL'),
    nullable=True
  )
  contact: Contact = relationship('Contact', foreign_keys=[id_contact])

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu', ondelete='CASCADE')
  )
  etudiant: Etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(debut: date, fin: date, contrat: str, niveau: str, id_entreprise: int, id_domaine: int, id_contact: int, id_etu: int, salaire: int = None):
    return Emploi(
      debut=debut, 
      fin=fin,
      contrat=contrat,
      salaire=salaire,
      niveau=niveau,
      id_entreprise=id_entreprise, 
      id_domaine=id_domaine, 
      id_contact=id_contact,
      id_etu=id_etu
    )

  def to_json(self, full = False):
    return {
      'id': self.id_emploi,
      'owner': self.etudiant if full else self.id_etu,
      'company': self.entreprise.to_json(),
      'referrer': self.contact,
      'domain': self.domaine.domaine,
      'from': self.debut,
      'to': self.fin,
      'type': self.contrat,
      'wage': self.salaire,
      'level': self.niveau,
    }
