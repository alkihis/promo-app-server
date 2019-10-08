from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship
from server import db
from Models.Formation import Formation
from datetime import date

class Etudiant(db):
  __tablename__ = "etudiant"

  id_etu = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  prenom = Column(String, nullable=False)
  mail = Column(String, nullable=False)
  birthdate = Column(Date, nullable=False)
  promo_entree = Column(String, nullable=False)
  promo_sortie = Column(String)

  cursus_anterieur = Column(Integer,
    ForeignKey('formation.id_form')
  )
  cursus_obj: Formation = relationship('Formation', foreign_keys=[cursus_anterieur])

  reorientation = Column(Integer,
   ForeignKey('formation.id_form')
  )
  reorientation_obj: Formation = relationship('Formation', foreign_keys=[reorientation])

  def __init__(self, **kwargs):
    super(Etudiant, self).__init__(**kwargs)
    self.is_authenticated = True
    self.is_active = True
    self.is_anonymous = False

  def get_id(self) -> str:
    return str(self.id_etu)

  @staticmethod
  def create(
    nom: str, 
    prenom: str, 
    mail: str, 
    birthdate: date, 
    promo_entree: str, 
    promo_sortie: str = None, 
    cursus_anterieur: int = None,
    reorientation: int = None
  ):
    return Etudiant(
      nom=nom, 
      prenom=prenom, 
      mail=mail, 
      birthdate=birthdate, 
      promo_entree=promo_entree,
      promo_sortie=promo_sortie,
      cursus_anterieur=cursus_anterieur,
      reorientation=reorientation
    )

  def to_json(self):
    return {
      'id': self.id_etu,
      'name': self.nom,
      'surname': self.prenom,
      'promo_in': self.promo_entree,
      'promo_out': self.promo_sortie,
      'email': self.mail,
      'previous_formation': None if not self.cursus_obj else self.cursus_obj.to_json(),
      'next_formation': None if not self.reorientation_obj else self.reorientation_obj.to_json()
    }
