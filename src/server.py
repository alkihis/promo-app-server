from flask import Flask
from helpers import cleanDb, DATABASE
from sqlalchemy import create_engine, Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

print("Cleaning database")
cleanDb()

engine = create_engine('sqlite:///' + DATABASE, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
db = declarative_base()
db.query = db_session.query_property()

app = Flask("promo-app-server")

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
  cursus_obj = relationship('Formation', foreign_keys=[cursus_anterieur])

  reorientation = Column(Integer,
   ForeignKey('formation.id_form')
  )
  reorientation_obj = relationship('Formation', foreign_keys=[reorientation])

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


class Formation(db):
  __tablename__ = "formation"

  id_form = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  lieu = Column(String, nullable=False)

  @staticmethod
  def create(nom: str, lieu: str):
    return Formation(nom=nom, lieu=lieu)


class Contact(db):
  __tablename__ = "contact"

  nom = Column(String, nullable=False)
  id_contact = Column(Integer, primary_key=True)
  mail = Column(String, nullable=False)

  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_form'),
    nullable=False
  )

  @staticmethod
  def create(nom: str, mail: str, id_entreprise: int):
    return Contact(nom=nom, mail=mail, id_entreprise=id_entreprise)


class Entreprise(db):
  __tablename__ = "entreprise"

  id_entreprise = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  ville = Column(String, nullable=False)
  taille = Column(String, nullable=False)
  statut = Column(String, nullable=False)

  @staticmethod
  def create(nom: str, ville: str, taille: str, statut: str):
    return Entreprise(
      nom=nom,
      ville=ville,
      taille=taille,
      statut=statut
    )


class Domaine(db):
  __tablename__ = "domaine"

  id_domaine = Column(Integer, primary_key=True)
  domaine = Column(String, nullable=False)

  @staticmethod
  def create(domaine: str):
    return Domaine(domaine=domaine)


class Stage(db):
  __tablename__ = "stage"

  id_stage = Column(Integer, primary_key=True)
  promo = Column(String, nullable=False)
  
  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_form'),
    nullable=False
  )
  entreprise = relationship('Entreprise', foreign_keys=[id_entreprise])

  id_domaine = Column(
    Integer,
    ForeignKey('domain.id_domaine'),
    nullable=False
  )
  domaine = relationship('Domaine', foreign_keys=[id_domaine])

  id_contact = Column(
    Integer,
    ForeignKey('contact.id_form'),
    nullable=False
  )
  contact = relationship('Contact', foreign_keys=[id_contact])

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu'),
    nullable=False
  )
  etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(promo: str, id_entreprise: int, id_domaine: int, id_contact: int, id_etu: int):
    return Stage(
      promo=promo, 
      id_entreprise=id_entreprise, 
      id_domaine=id_domaine, 
      id_contact=id_contact,
      id_etu=id_etu
    )
  

class Emploi(db):
  __tablename__ = "emploi"

  id_emploi = Column(Integer, primary_key=True)
  debut = Column(String, nullable=False)
  fin = Column(String, nullable=False)
  contrat = Column(String, nullable=False)
  salaire = Column(Integer)
  
  id_entreprise = Column(
    Integer,
    ForeignKey('entreprise.id_form')
  )
  entreprise = relationship('Entreprise', foreign_keys=[id_entreprise])

  id_domaine = Column(
    Integer,
    ForeignKey('domain.id_domaine')
  )
  domaine = relationship('Domaine', foreign_keys=[id_domaine])

  id_contact = Column(
    Integer,
    ForeignKey('contact.id_form')
  )
  contact = relationship('Contact', foreign_keys=[id_contact])

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu')
  )
  etudiant = relationship('Etudiant', foreign_keys=[id_etu])

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


class Token(db):
  __tablename__ = "token"

  token = Column(String, primary_key=True)

  type = Column(Boolean, nullable=False)

  id_etu = Column(
    Integer,
    ForeignKey('contact.id_form'),
    nullable=True
  )
  etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(token: str, type: int, id_etu: int = None):
    return Token(token=token, type=type, id_etu=id_etu)


db.metadata.create_all(bind=engine)
