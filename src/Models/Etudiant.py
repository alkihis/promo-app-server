from sqlalchemy import Integer, String, Boolean, Column, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Query
from server import db
from Models.Formation import Formation
from datetime import date, datetime

class Etudiant(db):
  __tablename__ = "etudiant"
  query: Query

  id_etu = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  prenom = Column(String, nullable=False)
  mail = Column(String, nullable=False)
  annee_entree = Column(String, nullable=False)
  annee_sortie = Column(String)
  entree_en_m1 = Column(Boolean, nullable=False)
  visible = Column(Boolean, nullable=False)
  diplome = Column(Boolean, nullable=False, default=False)
  derniere_modification = Column(DateTime, nullable=False)

  cursus_anterieur = Column(Integer,
    ForeignKey('formation.id_form', ondelete='SET NULL'),
    nullable=True
  )
  cursus_obj: Formation = relationship('Formation', foreign_keys=[cursus_anterieur])

  reorientation = Column(Integer,
    ForeignKey('formation.id_form', ondelete='SET NULL'),
    nullable=True
  )
  reorientation_obj: Formation = relationship('Formation', foreign_keys=[reorientation])

  def refresh_update(self):
    self.derniere_modification = datetime.now()

  @staticmethod
  def create(
    nom: str, 
    prenom: str, 
    mail: str, 
    annee_entree: str, 
    entree_en_m1: bool,
    annee_sortie: str = None, 
    cursus_anterieur: int = None,
    reorientation: int = None,
    diplome: bool = False,
    visible: bool = True
  ):
    return Etudiant(
      nom=nom, 
      prenom=prenom, 
      mail=mail,
      annee_entree=annee_entree,
      annee_sortie=annee_sortie,
      cursus_anterieur=cursus_anterieur,
      reorientation=reorientation,
      entree_en_m1=entree_en_m1,
      diplome=diplome,
      derniere_modification=datetime.now(),
      visible=visible
    )

  def to_json(self, full = False):
    etu = {
      'id': self.id_etu,
      'last_name': self.nom,
      'first_name': self.prenom,
      'year_in': self.annee_entree,
      'year_out': self.annee_sortie,
      'entered_in': "M1" if self.entree_en_m1 else "M2",
      'email': self.mail,
      'graduated': self.diplome,
      'previous_formation': None if not self.cursus_obj else self.cursus_obj.to_json(),
      'next_formation': None if not self.reorientation_obj else self.reorientation_obj.to_json(),
      'last_update': self.derniere_modification,
      'public': self.visible,
    }

    if full:
      # Import cyclique, ne peut être fait en haut du fichier
      from Models.Emploi import Emploi
      from Models.Stage import Stage
      
      emplois = Emploi.query.filter_by(id_etu=self.id_etu).all()
      etu['jobs'] = [e.to_json() for e in emplois]

      stages = Stage.query.filter_by(id_etu=self.id_etu).all()
      etu['internships'] = [e.to_json() for e in stages]

    return etu
