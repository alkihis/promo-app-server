from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Formation import Formation
from datetime import date

class Etudiant(db):
  __tablename__ = "etudiant"
  query: Query

  id_etu = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  prenom = Column(String, nullable=False)
  mail = Column(String, nullable=False)
  birthdate = Column(Date)
  annee_entree = Column(String, nullable=False)
  annee_sortie = Column(String)
  entree_en_m1 = Column(Boolean, nullable=False)

  cursus_anterieur = Column(Integer,
    ForeignKey('formation.id_form', ondelete='SET NULL')
  )
  cursus_obj: Formation = relationship('Formation', foreign_keys=[cursus_anterieur])

  reorientation = Column(Integer,
   ForeignKey('formation.id_form', ondelete='SET NULL')
  )
  reorientation_obj: Formation = relationship('Formation', foreign_keys=[reorientation])

  @staticmethod
  def create(
    nom: str, 
    prenom: str, 
    mail: str, 
    birthdate: date, 
    annee_entree: str, 
    entree_en_m1: bool,
    annee_sortie: str = None, 
    cursus_anterieur: int = None,
    reorientation: int = None
  ):
    return Etudiant(
      nom=nom, 
      prenom=prenom, 
      mail=mail, 
      birthdate=birthdate, 
      annee_entree=annee_entree,
      annee_sortie=annee_sortie,
      cursus_anterieur=cursus_anterieur,
      reorientation=reorientation,
      entree_en_m1=entree_en_m1
    )

  def to_json(self):
    return {
      'id': self.id_etu,
      'last_name': self.nom,
      'first_name': self.prenom,
      'year_in': self.annee_entree,
      'year_out': self.annee_sortie,
      'entered_in': "M1" if self.entree_en_m1 else "M2",
      'email': self.mail,
      'previous_formation': None if not self.cursus_obj else self.cursus_obj.to_json(),
      'next_formation': None if not self.reorientation_obj else self.reorientation_obj.to_json()
    }
