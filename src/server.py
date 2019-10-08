from flask import Flask
from helpers import cleanDb, DATABASE
from sqlalchemy import create_engine, Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import date
from json import JSONEncoder

##### Define a JSON encoder
""" Module that monkey-patches json module when it's imported so
JSONEncoder.default() automatically checks for a special "to_json()"
method and uses it to encode the object if found.
"""

def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = JSONEncoder.default  # Save unmodified default.
JSONEncoder.default = _default # Replace it.

##### End JSON encoder

# print("Cleaning database")
# cleanDb()

## Create SQL engine
engine = create_engine('sqlite:///' + DATABASE, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
db = declarative_base()
db.query = db_session.query_property()

### Create Flask Server
app = Flask("promo-app-server")

class Formation(db):
  __tablename__ = "formation"

  id_form = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  lieu = Column(String, nullable=False)

  @staticmethod
  def create(nom: str, lieu: str):
    return Formation(nom=nom, lieu=lieu)

  def to_json(self):
    return {
      'id': self.id_form,
      'name': self.nom,
      'location': self.lieu
    }


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


class Entreprise(db):
  __tablename__ = "entreprise"

  id_entreprise = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  ville = Column(String, nullable=False)
  taille = Column(String, nullable=False)
  statut = Column(String, nullable=False)

  stages = relationship('Stage', back_populates="entreprise")
  emplois = relationship('Emploi', back_populates="entreprise")

  @staticmethod
  def create(nom: str, ville: str, taille: str, statut: str):
    return Entreprise(
      nom=nom,
      ville=ville,
      taille=taille,
      statut=statut
    )
  
  def to_json(self):
    return {
      "id": self.id_entreprise,
      "name": self.nom,
      "town": self.ville,
      "size": self.taille,
      "status": self.statut
    }


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


class Domaine(db):
  __tablename__ = "domaine"

  id_domaine = Column(Integer, primary_key=True)
  domaine = Column(String, nullable=False)

  @staticmethod
  def create(domaine: str):
    return Domaine(domaine=domaine)

  def to_json(self):
    return {
      'id': self.id_domaine,
      'domaine': self.domain
    }


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
  

class Emploi(db):
  __tablename__ = "emploi"

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


class Token(db):
  __tablename__ = "token"

  token = Column(String, primary_key=True)

  type = Column(Boolean, nullable=False)

  id_etu = Column(
    Integer,
    ForeignKey('etudiant.id_etu'),
    nullable=True
  )
  etudiant: Etudiant = relationship('Etudiant', foreign_keys=[id_etu])

  @staticmethod
  def create(token: str, type: int, id_etu: int = None):
    return Token(token=token, type=type, id_etu=id_etu)

def init_db():
  db.metadata.create_all(bind=engine)
