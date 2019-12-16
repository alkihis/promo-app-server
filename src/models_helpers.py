from Models.Etudiant import Etudiant
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Stage import Stage
from Models.Emploi import Emploi
from Models.Contact import Contact
from Models.Formation import Formation
from Models.AskCreation import AskCreation
from helpers import get_user, is_teacher, get_request, convert_date, create_token_for, generate_login_link_for, generate_random_token
from typing import Optional, List, Tuple, Set
from errors import ERRORS
import urllib.parse
import re
import datetime
from datetime import date, timedelta
import requests
import sqlite3
import uuid
import zipfile
import json
from io import BytesIO
from server import db_session
from flask import send_file
import os
import jinja2
from gmail import GMAIL_SERVICE, send_message, create_message, MASTER_ADDRESS
from const import SITE_URL, STATIC_SITE_URL

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

      if not line.strip():
        continue

      parts: List[str] = line.strip().split('\t')

      try:
        first_name, last_name, email, graduation_year, is_in_m1, is_graduated = parts
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
        entree_en_m1=(is_in_m1 == "1"),
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


def create_ask_creation_token(mail: str, matches):
  ## Check if AskCreation already sended
  AskCreation.query.filter_by(mail=mail).delete()

  token = generate_random_token()

  a = AskCreation.create(token, mail)
  db_session.add(a)
  db_session.commit()

  return '<a href="' + SITE_URL + '/profile_create?token=' + str(a.token) + f'" target="_blank">{matches.group(1)}</a>'


def send_invite_create_profile_mail(mail: str):
  """
    Envoie un e-mail à un étudiant lui invitant à créer son profil
    sur l'application, via le lien contenu dans le mail.

    mail: Email auquel envoyer la demande de création
  """
  s: Etudiant = Etudiant.query.filter_by(mail=mail).one_or_none()

  if s:  
    # L'étudiant a déjà créé son profil, invitation à y aller plutôt
    return send_welcome_mail(s.id_etu)

  content = """
    {{ title Création de votre profil }}
    {{ subtitle Application de suivi des promotions du Master Bio-Informatique }}

    {{ strong promos@bioinfo }} est un service web vous permettant de renseigner des informations
    en lien avec votre master effectué à Lyon.

    {{ new_line }}

    En saisissant des données en rapport avec vos stages, contacts, lieux d'embauche et formations précédentes,
    vous aidez les promotions plus récentes grâce à vos données et participez à construire des statistiques sur
    les débouchés de la formation.

    {{ new_line }}

    {{ italic La majorité des données saisies sont uniquement visibles par les enseignants. }}

    {{ +subtitle }}
      {{ +center }}
        {{ profile_creation_link "Cliquez ici pour créer votre profil sur le service" }}
      {{ -center }}
    {{ -subtitle }}

    {{ subtitle Accès au site }}  

    {{ strong Vous recevez cet e-mail car un enseignant souhaite que vous créeiez et complétiez votre profil. }}

    {{ new_line }}

    La création de votre profil sur l'application vous donnera accès à un tableau de bord, où vous serez en mesure
    de saisir vos informations.

    {{ new_line }}
    {{ new_line }}

    {{ strong Merci pour votre participation ! }}
  """

  send_basic_mail(content, [mail], "Suivi des promotions du Master Bio-Informatique Lyon")


def send_ask_relogin_mail(student: int):
  """
    Envoie un e-mail à un étudiant lui invitant à se connecter 
    sur le site pour actualiser son profil via le lien contenu dans le mail.

    student: student ID
  """
  s: Etudiant = Etudiant.query.filter_by(id_etu=student).one_or_none()

  if not s:
    raise ValueError("Student not found")

  content = """
    {{ title Actualisation de votre profil }}
    {{ subtitle Application de suivi des promotions du Master Bio-Informatique }}

    Bonjour {{ +strong }}{{ studentFirstName }}{{ -strong }}, 
    {{ strong promos@bioinfo }} est un service web vous permettant de renseigner des informations
    en lien avec votre master effectué à Lyon.

    {{ new_line }}

    Cela fait un certain temps que l'on ne vous a pas vu sur la plateforme.
    Et si vous passiez nous dire ce que vous devenez ?

    {{ new_line }}

    {{ italic Vos informations nous aident à proposer une formation plus pertinente. }}

    {{ +subtitle }}
      {{ +center }}
        {{ auth_link "Cliquez ici pour vous connecter à votre profil" }}
      {{ -center }}
    {{ -subtitle }}

    {{ subtitle Accès au site }}  

    {{ +strong }}{{ student }}{{ -strong }}, pour vous connecter, suivez le lien de connexion ci-dessus.
    Il vous amène directement sur votre tableau de bord, où vous serez en mesure d'ajouter et
    actualiser toutes vos informations.

    {{ new_line }}
    {{ new_line }}

    {{ strong Merci pour votre participation ! }}
  """

  send_basic_mail(content, [s.mail], "Actualisation de votre profil - Suivi des promotions du Master Bio-Informatique")


def send_welcome_mail(student: int):
  """
    Envoie un e-mail à un étudiant lui invitant à se connecter 
    sur le site via le lien contenu dans le mail.

    student: student ID
  """
  s: Etudiant = Etudiant.query.filter_by(id_etu=student).one_or_none()

  if not s:
    raise ValueError("Student not found")

  content = """
    {{ title Connexion à votre compte }}
    {{ subtitle Application de suivi des promotions du Master Bio-Informatique }}

    {{ strong promos@bioinfo }} est un service web vous permettant de renseigner des informations
    en lien avec votre master effectué à Lyon.

    {{ new_line }}

    En saisissant des données en rapport avec vos stages, contacts, lieux d'embauche et formations précédentes,
    vous aidez les promotions plus récentes grâce à vos données et participez à construire des statistiques sur
    les débouchés de la formation.

    {{ new_line }}

    {{ italic La majorité des données saisies sont uniquement visibles par les enseignants. }}

    {{ +subtitle }}
      {{ +center }}
        {{ auth_link "Cliquez ici pour vous connecter automatiquement" }}
      {{ -center }}
    {{ -subtitle }}

    {{ subtitle Accès au site }}  

    {{ +strong }}{{ student }}{{ -strong }}, pour vous connecter, suivez le lien de connexion ci-dessus.
    Il vous amène directement sur votre tableau de bord, où vous serez en mesure d'ajouter et
    actualiser toutes vos informations.

    {{ new_line }}
    {{ new_line }}

    {{ strong Merci pour votre participation ! }}
  """

  send_basic_mail(content, [s.mail], "Connexion à l'application de suivi des promotions")


def preview_template(student: Etudiant, content: str, obj: str) -> str:
  """
    Prévisualise le résultat d'un template mail pour l'étudiant donné.

    student: Object Etudiant
  """

  return parse_mail_template(content, [student.mail], obj, as_message=False)[0]


def parse_mail_template(content: str, to: List[str], obj: str, as_message = True):
  """
    Parse et rend les mails pour les étudiants donnés.

    content: Template string

    to: Liste d'emails d'étudiants

    obj: Objet du message

    as_message: True si le message sera rendu avec create_message().
    Sinon, seule la template string modifiée sera retournée.

    @returns Liste de messages/template strings modifiées
  """

  dir_path = os.path.dirname(os.path.realpath(__file__)) + '/../templates/'
  mail_html = open(dir_path + 'mail.html', 'r').read()

  # Escape HTML
  content = re.sub("&", "&amp;", content)
  content = re.sub("<", "&lt;", content)
  content = re.sub(">", "&gt;", content)

  # Replacements HTML globaux
  content = re.sub(r'{{ *new_line *}}', "<br />", content)

  content = re.sub(r'{{ *title (.+?) *}}', r'<h1>\1</h1>', content, flags=re.S)
  content = re.sub(r'{{ *\+title *}}(.+?){{ *\-title *}}', r'<h1>\1</h1>', content, flags=re.S)

  content = re.sub(r'{{ *subtitle (.+?) *}}', r'<h3>\1</h3>', content, flags=re.S)
  content = re.sub(r'{{ *\+subtitle *}}(.+?){{ *\-subtitle *}}', r'<h3>\1</h3>', content, flags=re.S)
  
  content = re.sub(r'{{ *\+center *}}(.+?){{ *\-center *}}', r'<center>\1</center>', content, flags=re.S)

  content = re.sub(r'{{ *strong (.+?) *}}', r'<strong>\1</strong>', content, flags=re.S)
  content = re.sub(r'{{ *\+strong *}}(.+?){{ *\-strong *}}', r'<strong>\1</strong>', content, flags=re.S)

  content = re.sub(r'{{ *italic (.+?) *}}', r'<em>\1</em>', content, flags=re.S)
  content = re.sub(r'{{ *\+italic *}}(.+?){{ *\-italic *}}', r'<em>\1</em>', content, flags=re.S)

  content = re.sub(r'{{ *link (.+?) +\"(.+?)\" *}}', r'<a target="_blank" href="\1">\2</a>', content, flags=re.S)

  templates = []

  for student in to:
    s: Etudiant = Etudiant.query.filter_by(mail=student).one_or_none()
    
    text = content

    text = re.sub(r'{{ *profile_creation_link +\"(.+?)\" *}}', lambda matches: create_ask_creation_token(student, matches), text, flags=re.S)

    # Student data
    if s:
      text = re.sub(r'{{ *studentName *}}', s.nom, text)
      text = re.sub(r'{{ *studentFirstName *}}', s.prenom, text)
      text = re.sub(r'{{ *studentMail *}}', s.mail, text)
      text = re.sub(r'{{ *student *}}', str(s.prenom) + " " + str(s.nom), text)

      # Student-specific link
      text = re.sub(r'{{ *auth_link +\"(.+?)\" *}}', r'<a target="_blank" href="' + generate_login_link_for(s.id_etu) + r'">\1</a>', text, flags=re.S)

    # Utilise Jinja2 et pas Flask pour pouvoir envoyer
    # des e-mails hors contexte application
    template = jinja2.Template(mail_html)
    msg_content = template.render(content=text, subject=obj, site_url=SITE_URL, static_site_url=STATIC_SITE_URL)

    # Create the mail
    if as_message:
      # create_message(MASTER_ADDRESS, student, obj, msg_content)
      # DEBUG TODO remove
      templates.append(create_message(MASTER_ADDRESS, 'tulouca@gmail.com', obj, msg_content))
    else:
      templates.append(msg_content)
  
  return templates


def send_basic_mail(content: str, to: List[str], obj: str):
  templates = parse_mail_template(content, to, obj, as_message=True)

  for t in templates:
    # Send the mails
    send_message(GMAIL_SERVICE, "me", t)


def create_a_student(data, with_mail = True):
  # Si toutes ces clés ne sont pas présentes dans le dict
  if not {'first_name', 'last_name', 'email', 'year_in', 'entered_in', 'graduated'} <= set(data):
    return ERRORS.MISSING_PARAMETERS

  first_name, last_name, email = data['first_name'], data['last_name'], data['email']
  year_in, entree, diplome = data['year_in'], data['entered_in'], data['graduated']

  #### TODO check data of student !

  student_check = Etudiant.query.filter_by(mail=email).all()
  if len(student_check):
    return ERRORS.CONFLICT

  special_check = r"^[\w_ -]+$" 
  if not re.match(special_check,first_name):
    return ERRORS.INVALID_INPUT_VALUE

  if not re.match(special_check,last_name):
    return ERRORS.INVALID_INPUT_VALUE

  email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
  if not re.match(email_catch, email):
    return ERRORS.INVALID_INPUT_TYPE

  current_date = datetime.datetime.now().date().year

  if type(diplome) is not bool:
    return ERRORS.INVALID_INPUT_TYPE

  try:
    if int(year_in) > current_date or int(year_in) < 2015:
      return ERRORS.INVALID_DATE
  except:
    return ERRORS.INVALID_INPUT_TYPE

  
  # Create student
  etu = Etudiant.create(nom=last_name, prenom=first_name, mail=email, annee_entree=year_in, entree_en_m1=entree == "M1", diplome=diplome)

  db_session.add(etu)
  db_session.commit()

  # Create a token automatically and send the welcome e-mail
  if with_mail:
    send_welcome_mail(etu.id_etu)

  return etu


def escape(s):
  return str(s).replace('\t', ' ')


def student_as_csv(student: Etudiant = None, full = False):
  if not student:
    end = ""
    if full:
      end = '\t' + formation_as_csv() + '\t' + formation_as_csv(prefix="formation postérieure")

    return "ID Étudiant\tNom étudiant\tPrénom étudiant\tE-mail\tAnnée d'entrée\tAnnée de sortie\tEst diplômé\tEst entré en M1" + end

  annee_sortie = student.annee_sortie
  if not annee_sortie and student.diplome:
    if student.entree_en_m1:
      annee_sortie = student.annee_entree + 2
    else:
      annee_sortie = student.annee_entree + 1

  no_formation = "\t\t\t"

  return "\t".join(map(escape, [
    student.id_etu,
    student.nom,
    student.prenom,
    student.mail,
    student.annee_entree,
    annee_sortie if annee_sortie else "",
    "1" if student.diplome else "0",
    "1" if student.entree_en_m1 else "0"
  ])) + (("\t" + (formation_as_csv(student.cursus_obj) if student.cursus_anterieur else no_formation) + '\t' + \
         (formation_as_csv(student.reorientation_obj) if student.reorientation else no_formation)) if full else "")


def formation_as_csv(formation: Formation = None, prefix = "formation antérieure"):
  if not formation:
    return f"ID {prefix}\tFilière {prefix}\tLieu {prefix}\tNiveau {prefix}"

  return "\t".join(map(escape, [
    formation.id_form,
    formation.filiere,
    formation.lieu,
    formation.niveau,
  ]))


def job_as_csv(emploi: Emploi = None):
  if not emploi:
    return "ID Emploi\tType contrat\tDomaine\tNiveau\tDébut\tFin\tSalaire\t" + company_as_csv() + '\t' + contact_as_csv() + '\t' + student_as_csv()

  return "\t".join(map(escape, [
    emploi.id_emploi,
    emploi.contrat,
    emploi.domaine.nom,
    emploi.niveau,
    emploi.debut,
    emploi.fin if emploi.fin else '',
    emploi.salaire if emploi.salaire else '',
  ])) + "\t" + company_as_csv(emploi.entreprise) + '\t' + (contact_as_csv(emploi.contact) if emploi.id_contact else "\t\t") + '\t' + student_as_csv(emploi.etudiant)


def contact_as_csv(contact: Contact = None, full = False):
  if full:
    if not contact:
      return "ID Contact\tNom contact\tMail contact\t" + company_as_csv() 
    
    return "\t".join(map(escape, [
      contact.id_contact,
      contact.nom,
      contact.mail,
    ])) + "\t" + company_as_csv(contact.entreprise)

  if not contact:
    return "ID Contact\tNom contact\tMail contact"

  return "\t".join(map(escape, [
    contact.id_contact,
    contact.nom,
    contact.mail,
  ]))


def internship_as_csv(stage: Stage = None):
  if not stage:
    return "ID Stage\tAnnée du stage\tDomaine\t" + company_as_csv() + '\t' + contact_as_csv() + '\t' + student_as_csv()

  return "\t".join(map(escape, [
    stage.id_stage,
    stage.promo,
    stage.domaine.nom,
  ])) + "\t" + company_as_csv(stage.entreprise) + '\t' + (contact_as_csv(stage.contact) if stage.id_contact else "\t\t") + '\t' + student_as_csv(stage.etudiant)


def company_as_csv(entreprise: Entreprise = None):
  if not entreprise:
    return "ID Entreprise\tNom entreprise\tStatut entreprise\tTaille entreprise\tVille entreprise\tLatitude\tLongitude"

  return "\t".join(map(escape, [
    entreprise.id_entreprise,
    entreprise.nom,
    entreprise.statut,
    entreprise.taille,
    entreprise.ville,
    entreprise.lat,
    entreprise.lng,
  ]))


def export_all_data_in_csv(stu_ids: List[int] = None):
  if stu_ids:
    students: List[Etudiant] = Etudiant.query.filter(Etudiant.id_etu.in_(stu_ids)).all()
  else: 
    students: List[Etudiant] = Etudiant.query.all()

  # Référence toutes les entreprises, stages et emplois
  entreprises: Set[Entreprise] = set()
  emplois: Set[Emploi] = set()
  stages: Set[Stage] = set()
  contacts: Set[Contact] = set()
  formations: Set[Formation] = set()

  for student in students:
    if student.cursus_obj:
      formations.add(student.cursus_obj)
    if student.reorientation_obj:
      formations.add(student.reorientation_obj)

    e_all: List[Emploi] = Emploi.query.filter_by(id_etu=student.id_etu).all()
    for e in e_all:
      emplois.add(e)

      contact = e.contact
      entreprise = e.entreprise

      entreprises.add(entreprise)
      if contact:
        contacts.add(contact)

    s_all: List[Stage] = Stage.query.filter_by(id_etu=student.id_etu).all()
    for s in s_all:
      stages.add(s)

      contact = s.contact
      entreprise = s.entreprise

      entreprises.add(entreprise)
      if contact:
        contacts.add(contact)

  # On a tous les stages, emplois, toutes les entreprises et tous les contacts
  # Crée le csv
  zip_io = BytesIO()
  zip_file = zipfile.ZipFile(zip_io, 'w', compression=zipfile.ZIP_DEFLATED)

  tmp_csv = student_as_csv(full=True) + "\n"
  for student in students:
    tmp_csv += student_as_csv(student, full=True) + "\n"

  zip_file.writestr('etudiants.csv', tmp_csv)

  tmp_csv = formation_as_csv() + "\n"
  for formation in formations:
    tmp_csv += formation_as_csv(formation) + "\n"

  zip_file.writestr('formations.csv', tmp_csv)

  tmp_csv = company_as_csv() + "\n"
  for entreprise in entreprises:
    tmp_csv += company_as_csv(entreprise) + "\n"

  zip_file.writestr('entreprises.csv', tmp_csv)

  tmp_csv = job_as_csv() + "\n"
  for emploi in emplois:
    tmp_csv += job_as_csv(emploi) + "\n"

  zip_file.writestr('emplois.csv', tmp_csv)

  tmp_csv = internship_as_csv() + "\n"
  for stage in stages:
    tmp_csv += internship_as_csv(stage) + "\n"

  zip_file.writestr('stages.csv', tmp_csv)

  tmp_csv = contact_as_csv(full=True) + "\n"
  for contact in contacts:
    tmp_csv += contact_as_csv(contact, full=True) + "\n"

  zip_file.writestr('contacts.csv', tmp_csv)
  zip_file.close()

  zip_io.seek(0)

  return send_file(zip_io, attachment_filename='export.zip', as_attachment=True)


def ask_refresh_to_students(min_month = 3):
  """
    Demande aux étudiants qui n'ont pas actualisé leur profil depuis {min_month}
    de l'actualiser via e-mail.
  """

  # Recherche les étudiants ayant pas mis à jour depuis
  # au moins min_month
  delta = timedelta(days=min_month*30)
  max_date = date.today() - delta

  students: List[Etudiant] = Etudiant.query.filter(Etudiant.derniere_modification < max_date).all()
  
  for student in students:
    send_ask_relogin_mail(student.id_etu)

