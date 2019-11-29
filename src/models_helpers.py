from Models.Etudiant import Etudiant
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Stage import Stage
from Models.Emploi import Emploi
from Models.Contact import Contact
from helpers import get_user, is_teacher, get_request, convert_date, create_token_for
from typing import Optional, List, Tuple
from errors import ERRORS
import urllib.parse
import re
import datetime
import requests
import sqlite3
import json
from server import db_session

def get_etu_object_for_logged_user() -> Optional[Etudiant]:
  user = get_user()

  if user and user.id_etu:
    return Etudiant.query.filter_by(id_etu=user.id_etu).one_or_none()

def get_student_or_none() -> Optional[Etudiant]:
  r = get_request()

  if is_teacher():
    if r.args.get('id') or r.args.get('user_id'):
      try:
        u_id = r.args.get('id') if r.args.get('id') else r.args.get('user_id')
        return Etudiant.query.filter_by(id_etu=int(u_id)).one_or_none()
      except:
        return None
    elif r.is_json and 'id' in r.json or 'user_id' in r.json:
      try:
        u_id = r.json['id'] if 'id' in r.json else r.json['user_id']
        return Etudiant.query.filter_by(id_etu=int(u_id)).one_or_none()
      except:
        return None
  else:
    return get_etu_object_for_logged_user()


def refresh_locations_of_company():
  companies: List[Entreprise] = Entreprise.query.filter_by(lat=None).all()

  for c in companies:
    print("Fetching company " + str(c.ville))
    coords = get_location_of_company(str(c.ville), True)
    c.lat = coords[0]
    c.lng = coords[1]

  db_session.commit()


def get_location_of_company(loc: str, force = False) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """
    Retourne un couple [latitude, longitude] pour une localisation donnée.
    Si aucune localisation trouvé, renvoie [None, None]
  """
  companies: List[Entreprise] = Entreprise.query.filter_by(ville=loc).all()

  if len(companies):
    tuple_loc = (companies[0].lat, companies[0].lng, companies[0].ville)

    if force and tuple_loc[0] is None:
      pass
    else:
      return tuple_loc

  # Download from OSM
  loc_quoted = urllib.parse.quote(loc)
  url = "https://nominatim.openstreetmap.org/search?q=" + loc_quoted + "&format=json"
  print(f'Recherche du lieu {loc} sur OpenStreetMap')

  content = requests.get(url)

  try:
    content = content.json()
  except:
    return (None, None, loc)

  # Ne considère que la première
  if not len(content):
    return (None, None, loc)

  display_name: str = content[0]['display_name']
  splitted = display_name.split(',')
  town = splitted[0].strip()
  region = splitted[1].strip();
  land = splitted[-1].strip()
  
  full_name = ", ".join([town, region, land])

  return (content[0]['lat'], content[0]['lon'], full_name)


def import_students_from_file(filename: str):
  """
    Import base file for populating students
    Student line must be:

    first_name  last_name email graduation_year  is_graduated(1/0)
  """
  with open(filename) as fp:
    i = 0
    for line in fp:
      i += 1
      parts: List[str] = line.strip().split('\t')

      try:
        first_name, last_name, email, graduation_year, is_graduated = parts
      except:
        print(f"Invalid line {i}: Incorrect number of elements in line.")
        continue

      try:
        year_in = int(graduation_year) - 2
        graduation_year = int(graduation_year)

        if graduation_year < 2015:
          raise ValueError("Invalid gradutation date")
      except:
        print(f"Invalid line {i}: Graduation year is not valid ({graduation_year}).")
        continue

      e: Etudiant = Etudiant.query.filter_by(mail=email).one_or_none()
      if e:
        print(f"Line {i}: Student already exists (conflict in e-mail address)")
        continue

      etu = Etudiant.create(
        nom=last_name, 
        prenom=first_name, 
        mail=email, 
        annee_entree=year_in, 
        annee_sortie=graduation_year,
        diplome=(is_graduated == "1")
      )  

      db_session.add(etu)

  db_session.commit()


def import_domain_from_file(filename: str):
  """
    Import base file for populating domain table
    Domain line must be:

    internal_name  display_name
  """

  with open(filename) as fp:
    i = 0
    for line in fp:
      i += 1
      parts: List[str] = line.strip().split('\t')

      try:
        domain, name = parts
      except:
        print(f"Invalid line {i}: Incorrect number of elements in line.")
        continue

      d: Domaine = Domaine.query.filter_by(domaine=domain).all()

      if len(d):
        continue

      d = Domaine.create(domaine=domain, nom=name)
      db_session.add(d)

  db_session.commit()


def global_export(filename: str):
  final = {
    "students": Etudiant.query.all(),
    "companies": Entreprise.query.all(),
    "domains": Domaine.query.all(),
    "jobs": Emploi.query.all(),
    "internships": Stage.query.all(),
    "contacts": Contact.query.all(),
  }

  json.dump(final, open(filename, "w"))


def import_legacy_db(filename: str):
  with sqlite3.connect(filename) as conn:
    cur = conn.cursor()

    # Initialise les domaines
    doms = cur.execute('''
      SELECT nomDomaine FROM Domaine
    ''').fetchall()

    for d in doms:
      domaine = d[0]
      orm_domaine = Domaine.create(domaine, domaine)
      db_session.add(orm_domaine)

    db_session.commit()

    # Insertion des étudiants
    students: List[Tuple[str, str, str, str]] = cur.execute('''
      SELECT DISTINCT e.emailetu, nometu, prenometu, annee 
      FROM Etudiant e 
      JOIN Promo p
      ON e.emailetu=p.emailetu
    ''').fetchall()

    town_to_real_loc = {}

    emails = set()
    for student in students:
      email, nom, prenom, annee = student

      if email in emails:
        continue

      emails.add(email)

      year_out = annee.split('/')[1]
      year_in = str(int(year_out) - 2)

      e = Etudiant.create(
        nom=nom, 
        prenom=prenom, 
        mail=email, 
        annee_entree=year_in, 
        annee_sortie=year_out, 
        entree_en_m1=True,
        diplome=True
      )

      db_session.add(e)

    db_session.commit()
    # Insertion des emplois
    promo: List[Tuple[str, str, str, str, str, str, str, str, int]] = cur.execute(''' 
      SELECT annee, emailetu, remuneration, nomorga, lieu, contrat, datedebut, statut, nomdomaine, idExp
      FROM Promo 
      NATURAL JOIN Embauche
      NATURAL JOIN Organisation
      NATURAL JOIN Experience
      NATURAL JOIN InsertionPro
      NATURAL JOIN ExpDom
      NATURAL JOIN Domaine
    ''').fetchall()

    exps = set()    
    for experience in promo:
      annee, email, remuneration, nomorga, lieu, contrat, datedebut, statut, domaine, id_exp = experience

      if id_exp in exps:
        continue

      exps.add(id_exp)

      remuneration = int(remuneration)
      if remuneration == 0:
        remuneration = None
      else:
        remuneration *= 12

      # Cherche si nomorga existe
      companies: List[Entreprise] = Entreprise.query.filter_by(nom=nomorga).all()
      if len(companies):
        selected = companies[0]
      else:
        original_lieu = lieu
        if lieu in town_to_real_loc:
          lieu = town_to_real_loc[lieu]
        
        gps_coords = get_location_of_company(lieu, force=True)
        town_to_real_loc[original_lieu] = gps_coords[2]

        selected = Entreprise.create(
          nom=nomorga,
          ville=gps_coords[2],
          taille="small",
          statut="public",
          lat=gps_coords[0],
          lng=gps_coords[1]
        )

        db_session.add(selected)
        db_session.commit()

      jb = Emploi.create(
        debut=convert_date(datedebut),
        fin=None,
        contrat=convert_contrat(contrat),
        niveau=convert_level(statut),
        id_entreprise=selected.id_entreprise,
        id_domaine=Domaine.query.filter_by(nom=domaine).one_or_none().id_domaine,
        id_contact=None,
        id_etu=Etudiant.query.filter_by(mail=email).one_or_none().id_etu,
        salaire=remuneration
      )

      db_session.add(jb)

    # Insertion des stages
    stages: List[Tuple[str, str, str, str, str, str, str, str]] = cur.execute(''' 
      SELECT emailetu, nomorga, lieu, nomdomaine, typestage, idExp, nomtut, emailtut
      FROM Promo 
      NATURAL JOIN Embauche
      NATURAL JOIN Organisation
      NATURAL JOIN Experience
      NATURAL JOIN Stage s
      NATURAL JOIN ExpDom
      NATURAL JOIN Domaine
      LEFT JOIN Dirige d
      ON d.idS=s.idS
      NATURAL JOIN TUTEUR
    ''').fetchall()
    for stage in stages:
      emailetu, nomorga, lieu, domaine, typestage, id_exp, nom_tuteur, email_tuteur = stage
      
      etu: Etudiant = Etudiant.query.filter_by(mail=emailetu).one_or_none()

      if not etu:
        continue
      # Cherche si nomorga existe
      companies: List[Entreprise] = Entreprise.query.filter_by(nom=nomorga).all()
      if len(companies):
        selected = companies[0]
      else:
        original_lieu = lieu
        if lieu in town_to_real_loc:
          lieu = town_to_real_loc[lieu]

        gps_coords = get_location_of_company(lieu, force=True)
        town_to_real_loc[original_lieu] = gps_coords[2]

        selected = Entreprise.create(
          nom=nomorga,
          ville=gps_coords[2],
          taille="small",
          statut="public",
          lat=gps_coords[0],
          lng=gps_coords[1]
        )

        db_session.add(selected)
        db_session.commit()

      promo = int(str(etu.annee_entree))
      if typestage == "M1" or typestage == "volontaire":
        promo += 1
      else:
        promo += 2

      promo = str(promo)

      tuteur = None
      if email_tuteur:
        tuteur: Contact = Contact.query.filter_by(mail=email_tuteur).one_or_none()
        if not tuteur:
          tuteur = Contact.create(
            mail=email_tuteur,
            nom=nom_tuteur,
            id_entreprise=selected.id_entreprise
          )

          db_session.add(tuteur)
          db_session.commit()

      s = Stage.create(
        promo=promo,
        id_entreprise=selected.id_entreprise,
        id_domaine=Domaine.query.filter_by(nom=domaine).one_or_none().id_domaine,
        id_contact=(tuteur.id_contact if tuteur else None),
        id_etu=etu.id_etu
      )

      db_session.add(s)

    db_session.commit()


def convert_contrat(contrat: str):
  old_to_new = {
    'doctorat': 'these',
    'alternance': 'alternance',
    'CDI': 'cdi',
    'CDD': 'cdd',
  }
  return old_to_new[contrat]


def convert_level(level: str):
  old_to_new = {
    'Ingénieur': 'ingenieur',
    'Alternant': 'alternant',
    'Doctorant': 'doctorant',
  }
  return old_to_new[level]


def send_basic_mail(content: str, to: List[str], obj: str):
  # TODO interpolation de \student (par exemple)

  for student in to:
    # todo send the mail
    pass


def create_a_student(data):
  # Si toutes ces clés ne sont pas présentes dans le dict
  if not {'first_name', 'last_name', 'email', 'year_in', 'entered_in', 'graduated'} <= set(data):
    return ERRORS.MISSING_PARAMETERS

  first_name, last_name, email = data['first_name'], data['last_name'], data['email']
  year_in, entree, diplome = data['year_in'], data['entered_in'], data['graduated']

  # Do not forget to change datestring to date object !
  # birthdate = convert_date(birthdate)

  student_check = Etudiant.query.filter_by(mail=email).all()
  if len(student_check):
    return ERRORS.CONFLICT

  email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
  if not re.match(email_catch, email):
    return ERRORS.BAD_REQUEST

  current_date = datetime.datetime.now().date().year

  if type(diplome) is not bool:
    return ERRORS.BAD_REQUEST

  try:
    if int(year_in) > current_date or int(year_in) < 2015:
      return ERRORS.BAD_REQUEST
  except:
    return ERRORS.BAD_REQUEST
  
  # Create student
  etu = Etudiant.create(nom=last_name, prenom=first_name, mail=email, annee_entree=year_in, entree_en_m1=entree == "M1", diplome=diplome)

  db_session.add(etu)
  db_session.commit()

  # Create a token automatically
  create_token_for(etu.id_etu, teacher=False)

  return etu

