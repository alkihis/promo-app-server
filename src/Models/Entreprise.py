from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import relationship, Query
from server import db
from enum import Enum

class Entreprise(db):
  __tablename__ = "entreprise"
  query: Query

  id_entreprise = Column(Integer, primary_key=True)
  nom = Column(String, nullable=False)
  ville = Column(String, nullable=False)
  taille = Column(String, nullable=False)
  statut = Column(String, nullable=False)
  lat = Column(String)
  lng = Column(String)

  stages = relationship('Stage', back_populates="entreprise")
  emplois = relationship('Emploi', back_populates="entreprise")

  @staticmethod
  def create(nom: str, ville: str, taille: str, statut: str, lat: str = None, lng: str = None):
    return Entreprise(
      nom=nom,
      ville=ville,
      taille=taille,
      statut=statut,
      lat=lat,
      lng=lng
    )
  
  def to_json(self):
    return {
      "id": self.id_entreprise,
      "name": self.nom,
      "town": self.ville,
      "size": self.taille,
      "status": self.statut
    }
