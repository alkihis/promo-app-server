CREATE TABLE Etudiant (
  id_etu INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL,
  mail TEXT NOT NULL,
  promo_entree TEXT NOT NULL,
  promo_sortie TEXT,
  
  cursus_anterieur INTEGER,

  FOREIGN KEY(cursus_anterieur) REFERENCES Formation(id_form)
);

CREATE TABLE Formation (
  id_form INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL
);

CREATE TABLE Contact (
  id_contact INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL,
  mail TEXT NOT NULL
);

CREATE TABLE Entreprise (
  id_entreprise INTEGER PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL,
  ville TEXT NOT NULL,
  taille TEXT NOT NULL, -- ENUM: Must be "" TODO DEFINE ENUM
  statut TEXT NOT NULL -- ENUM: Must be "PUBLIC" or "PRIVATE"
);

CREATE TABLE Domaine (
  id_domaine INTEGER PRIMARY KEY AUTOINCREMENT,
  domaine TEXT NOT NULL
);

CREATE TABLE Alternance (
  id_alt INTEGER PRIMARY KEY AUTOINCREMENT,

  promo TEXT NOT NULL,

  id_entreprise INTEGER NOT NULL,
  id_contact INTEGER NOT NULL,

  FOREIGN KEY(id_entreprise) REFERENCES Entreprise(id_entreprise),
  FOREIGN KEY(id_contact) REFERENCES Contact(id_contact)
);

CREATE TABLE Stage (
  id_stage INTEGER PRIMARY KEY AUTOINCREMENT,

  promo TEXT NOT NULL,

  id_etu INTEGER NOT NULL,
  id_contact INTEGER NOT NULL,
  id_domaine INTEGER NOT NULL,
  id_entreprise INTEGER NOT NULL,

  FOREIGN KEY(id_etu) REFERENCES Etudiant(id_etu),
  FOREIGN KEY(id_contact) REFERENCES Contact(id_contact),
  FOREIGN KEY(id_domaine) REFERENCES Domaine(id_domaine),
  FOREIGN KEY(id_entreprise) REFERENCES Entreprise(id_entreprise)
);

CREATE TABLE Emploi (
  id_emploi INTEGER PRIMARY KEY AUTOINCREMENT,
  id_etu INTEGER NOT NULL,
  id_contact INTEGER NOT NULL,
  id_domaine INTEGER NOT NULL,
  id_entreprise INTEGER NOT NULL,

  debut TEXT NOT NULL, -- DATETIME
  fin TEXT NOT NULL, -- DATETIME or "now"
  contrat TEXT NOT NULL, -- ENUM "CDD" "CDI" "These" TODO VOIR CONTRATS
  salaire INTEGER, -- Peut être non précisé

  FOREIGN KEY(id_etu) REFERENCES Etudiant(id_etu),
  FOREIGN KEY(id_contact) REFERENCES Contact(id_contact),
  FOREIGN KEY(id_domaine) REFERENCES Domaine(id_domaine),
  FOREIGN KEY(id_entreprise) REFERENCES Entreprise(id_entreprise)
);
