from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant

class Emploi(db):
  __tablename__ = "emploi"
  query: Query

  id_emploi = Column(Integer, primary_key=True)
  debut = Column(String, nullable=False)
  fin = Column(String, nullable=False)
  contrat = Column(String, nullable=False)
  salaire = Column(Integer)
  
  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_entreprise')
  )
  entreprise: Entreprise = relationship('Entreprise', back_populates="emplois")

  id_domaine = Column(
    Integer,
    ForeignKey('domaine.id_domaine')
  )
  domaine: Domaine = relationship('Domaine', foreign_keys=[id_domaine])

  id_contact = Column(
    Integer,
    ForeignKey('contact.id_contact')
  )
  contact: Contact = relationship('Contact', foreign_keys=[id_contact])

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu')
  )
  etudiant: Etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(debut: str, fin: str, contrat: str, id_entreprise: int, id_domaine: int, id_contact: int, id_etu: int, salaire: int = None):
    return Emploi(
      debut=debut, 
      fin=fin,
      contrat=contrat,
      salaire=salaire,
      id_entreprise=id_entreprise, 
      id_domaine=id_domaine, 
      id_contact=id_contact,
      id_etu=id_etu
    )

  def to_json(self):
    return {
      'id': self.id_emploi,
      'owner': self.etudiant,
      'company': self.entreprise,
      'referrer': self.contact,
      'domain': self.domaine.domaine,
      'from': self.debut,
      'to': self.fin,
      'type': self.contrat,
      'wage': self.salaire
    }
