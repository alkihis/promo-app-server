from sqlalchemy import Integer, String, Boolean, Column, Date, ForeignKey
from sqlalchemy.orm import relationship
from server import db

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
