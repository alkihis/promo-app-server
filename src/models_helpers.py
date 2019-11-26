from Models.Etudiant import Etudiant
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Stage import Stage
from Models.Emploi import Emploi
from Models.Contact import Contact
from helpers import get_user, is_teacher, get_request
from typing import Optional, List, Tuple
import urllib.parse
import requests
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


def get_location_of_company(loc: str, force = False) -> Tuple[Optional[str], Optional[str]]:
  """
    Retourne un couple [latitude, longitude] pour une localisation donnée.
    Si aucune localisation trouvé, renvoie [None, None]
  """
  companies: List[Entreprise] = Entreprise.query.filter_by(ville=loc).all()

  if len(companies):
    tuple_loc = (companies[0].lat, companies[0].lng)

    if force and tuple_loc[0] is None:
      pass
    else:
      return tuple_loc

  # Download from OSM
  loc_quoted = urllib.parse.quote(loc)
  url = "https://nominatim.openstreetmap.org/search?q=" + loc_quoted + "&format=json"

  content = requests.get(url)

  try:
    content = content.json()
  except:
    return (None, None)

  # Ne considère que la première
  if not len(content):
    return (None, None)

  return (content[0]['lat'], content[0]['lon'])


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

def send_basic_mail(content: str, to: List[str], obj: str):
  # TODO interpolation de \student (par exemple)

  for student in to:
    # todo send the mail
    pass

