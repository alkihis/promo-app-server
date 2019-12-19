-- noinspection SqlNoDataSourceInspectionForFile

CREATE TABLE Etudiant (
  id_etu INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL,
  prenom TEXT NOT NULL,
  mail TEXT NOT NULL,
  derniere_modification DATETIME NOT NULL,
  annee_entree TEXT NOT NULL,
  annee_sortie TEXT,
  entree_en_m1 BOOLEAN NOT NULL,
  diplome BOOLEAN NOT NULL DEFAULT FALSE,
  visible BOOLEAN NOT NULL DEFAULT FALSE,
  recoit_mail_auto BOOLEAN NOT NULL DEFAULT TRUE,
  
  cursus_anterieur INTEGER,
  reorientation INTEGER,

  FOREIGN KEY(cursus_anterieur) REFERENCES Formation(id_form) ON DELETE SET NULL,
  FOREIGN KEY(reorientation) REFERENCES Formation(id_form) ON DELETE SET NULL
);

CREATE TABLE Formation (
  id_form INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  lieu TEXT NOT NULL,
  niveau TEXT NOT NULL, -- ENUM: must be "Licence", "Master", "Doctorat", "Autre"
  filiere TEXT NOT NULL
);

CREATE TABLE Contact (
  id_contact INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL,
  mail TEXT NOT NULL,

  id_entreprise INTEGER NOT NULL,

  FOREIGN KEY(id_entreprise) REFERENCES Entreprise(id_entreprise) ON DELETE CASCADE
);

CREATE TABLE Entreprise (
  id_entreprise INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  nom TEXT NOT NULL,
  ville TEXT NOT NULL,
  taille TEXT NOT NULL, -- ENUM: Must be "small" , "medium", "big", "very_big"
  statut TEXT NOT NULL, -- ENUM: Must be "PUBLIC" or "PRIVATE"
  lat TEXT NOT NULL,
  lng TEXT NOT NULL
);

CREATE TABLE Domaine (
  id_domaine INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  domaine TEXT NOT NULL,
  nom TEXT NOT NULL
);

CREATE TABLE Stage (
  id_stage INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,

  promo TEXT NOT NULL,

  id_etu INTEGER NOT NULL,
  id_contact INTEGER NOT NULL,
  id_domaine INTEGER NOT NULL,
  id_entreprise INTEGER NOT NULL,

  FOREIGN KEY(id_etu) REFERENCES Etudiant(id_etu) ON DELETE CASCADE,
  FOREIGN KEY(id_contact) REFERENCES Contact(id_contact) ON DELETE SET NULL,
  FOREIGN KEY(id_domaine) REFERENCES Domaine(id_domaine) ON DELETE SET NULL,
  FOREIGN KEY(id_entreprise) REFERENCES Entreprise(id_entreprise) ON DELETE SET NULL
);

CREATE TABLE Emploi (
  id_emploi INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  id_etu INTEGER NOT NULL,
  id_contact INTEGER,
  id_domaine INTEGER NOT NULL,
  id_entreprise INTEGER NOT NULL,

  debut TEXT NOT NULL, -- DATETIME | promotion si alternance
  fin TEXT, -- DATETIME or "now" or null si pas fini
  contrat TEXT NOT NULL, -- ENUM "CDD" "CDI" "These" "Alternance"
  salaire INTEGER, -- Peut être non précisé
  niveau TEXT NOT NULL,

  FOREIGN KEY(id_etu) REFERENCES Etudiant(id_etu) ON DELETE CASCADE,
  FOREIGN KEY(id_contact) REFERENCES Contact(id_contact) ON DELETE SET NULL,
  FOREIGN KEY(id_domaine) REFERENCES Domaine(id_domaine) ON DELETE SET NULL,
  FOREIGN KEY(id_entreprise) REFERENCES Entreprise(id_entreprise) ON DELETE SET NULL
);

CREATE TABLE Token (
  token TEXT NOT NULL PRIMARY KEY,
  id_etu INTEGER,
  teacher INTEGER, -- 1 for teacher, 0 for student

  FOREIGN KEY(id_etu) REFERENCES Etudiant(id_etu) ON DELETE CASCADE
);
