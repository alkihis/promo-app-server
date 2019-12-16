import sqlite3
import os
import sys

# MIGRATION ANCIENNE BASE > CSV. NE PAS UTILISER

if len(sys.argv) < 2:
  print("Le nom de la base de données à exporter est requis")
  exit()

filename_export = "export.csv"
filename_import = sys.argv[1]

if len(sys.argv) > 2:
  filename_export = sys.argv[2]

try:
  db = sqlite3.connect(filename_import)
except:
  print("Impossible de se connecter à la base de données " + filename_import)
  exit()

try:
  fp = open(filename_export, 'w')
except:
  print(f"Impossible d'ouvrir le fichier de sortie {filename_export}. Vérifiez les droits.")
  exit()

students = db.execute('''
  SELECT id_etu, nom, prenom, mail, annee_entree, entree_en_m1, diplome FROM Etudiant
''').fetchall()

for student in students:
  id_etu, nom, prenom, mail, annee_entree, entree_en_m1, diplome = student

  annee_entree = str(annee_entree)
  entree_en_m1 = "1" if entree_en_m1 else "0"
  diplome = "1" if diplome else "0"

  fp.write(f"{nom}\t{prenom}\t{mail}\t{annee_entree}\t{entree_en_m1}\t{diplome}\n")

db.close()
