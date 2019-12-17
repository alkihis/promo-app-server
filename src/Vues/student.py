import flask
from Models.Etudiant import Etudiant
from Models.Formation import Formation
from Models.Entreprise import Entreprise
from Models.Emploi import Emploi
from Models.Stage import Stage
from Models.Token import Token
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, create_token_for, convert_date, is_truthy
from models_helpers import get_student_or_none, send_basic_mail, create_a_student, send_welcome_mail, send_ask_relogin_mail
from errors import ERRORS
from server import db_session, engine
from sqlalchemy import and_, or_
import datetime
import re
from typing import List, Dict
### Vues pour l'API /student

def student_routes(app: flask.Flask):
  # Get logged student
  @app.route('/student/self')
  @login_required
  def get_self_logged():
    if is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    return flask.jsonify(get_student_or_none())

  @app.route('/student/all')
  @login_required
  def get_all_students():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    full = False

    r = get_request()
    if 'full' in r.args:
      full = is_truthy(r.args['full'])

    if not full:
      return flask.jsonify(Etudiant.query.all())

    all_stu = [e.to_json(full) for e in Etudiant.query.all()]

    companies = {}
    for student in all_stu:
      for job in student['jobs']:
        if job['company']['id'] not in companies:
          companies[job['company']['id']] = job['company']
        
        job['company'] = job['company']['id']
        

      for internship in student['internships']:
        if internship['company']['id'] not in companies:
          companies[internship['company']['id']] = internship['company']

        internship['company'] = internship['company']['id']

    return flask.jsonify({ 'students': all_stu, 'companies': companies })

  # Get a single Etudiant by ID
  @app.route('/student/<int:id>', methods=["GET"])
  def get_id(id: int):
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS
    
    e: Etudiant = Etudiant.query.filter_by(id_etu=id).one_or_none()

    if not e:
      return ERRORS.STUDENT_NOT_FOUND

    return flask.jsonify(e)

  @app.route('/student/create', methods=['POST'])
  @login_required
  def create_student():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    # Check for content type
    r = get_request()
    if not r.is_json:
      return ERRORS.BAD_REQUEST

    # Check presence of required arguments
    # Required are first_name, last_name, email, year_in, birthdate 
    data = r.json

    etu = create_a_student(data)

    if type(etu) is not Etudiant:
      return etu # This is an error

    # Return the newly created student
    return flask.jsonify(etu)


  @app.route('/student/modify', methods=['POST'])
  @login_required
  def update_student():
    r = get_request()
    student = get_student_or_none()

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    if not student:
      return ERRORS.STUDENT_NOT_FOUND

    data = r.json

    if 'first_name' in data:
      special_check = r"^[\w_ -]+$" 
      if not re.match(special_check,data['first_name']):
        return ERRORS.INVALID_INPUT_VALUE

      student.prenom = data['first_name']

    if 'last_name' in data:
      special_check = r"^[\w_ -]+$" 
      if not re.match(special_check,data['last_name']):
        return ERRORS.INVALID_INPUT_VALUE

      student.nom = data['last_name']

    if 'year_in' and 'year_out' in data:
      try:
        year_in = int(data['year_in'])
      except:
        return ERRORS.INVALID_DATE
      
      try:
        year_out = int(data['year_out'])
      except:
        return ERRORS.INVALID_DATE
                  
      if year_in > year_out:
        return ERRORS.INVALID_DATE

      student.annee_entree = data['year_in']
      student.annee_sortie = data['year_out']

    if 'public' in data and type(data['public']) is bool:
      student.visible = data['public']

    if 'year_in' in data:
      try:
        year_in = int(data['year_in'])
      except:
        return ERRORS.INVALID_DATE

      if student.annee_sortie and year_in >= int(student.annee_sortie):
        return ERRORS.INVALID_DATE
      
      student.annee_entree = data['year_in']

    if 'year_out' in data:
      if data['year_out'] is None:
        student.annee_sortie = None
      else:
        try:
            year_out = int(data['year_out'])
        except:
          return ERRORS.INVALID_DATE

        if int(student.annee_entree) >= year_out:
          return ERRORS.INVALID_DATE

        student.annee_sortie = data['year_out']

    if 'email' in data:
      email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
      if not re.match(email_catch, data['email']):
        return ERRORS.INVALID_EMAIL

      student.mail = data['email']
      
    if 'previous_formation' in data:
      if type(data['previous_formation']) == int:
        # Check existance of formation
        desired = Formation.query.filter_by(id_form=data['previous_formation']).one_or_none()

        if desired:
          student.cursus_anterieur = data['previous_formation']
        else:
          db_session.rollback()
          return ERRORS.FORMATION_NOT_FOUND
      elif data['previous_formation'] is None:
        student.cursus_anterieur = None
      else:
        db_session.rollback()
        return ERRORS.INVALID_INPUT_TYPE
    if 'next_formation' in data:
      if type(data['next_formation']) == int:
        # Check existance of formation
        desired = Formation.query.filter_by(id_form=data['next_formation']).one_or_none()

        if desired:
          student.reorientation = data['next_formation']
        else:
          db_session.rollback()
          return ERRORS.FORMATION_NOT_FOUND
      elif data['next_formation'] is None:
        student.reorientation = None
      else:
        db_session.rollback()
        return ERRORS.INVALID_INPUT_TYPE
    if 'entered_in' in data:
      if data['entered_in'] != 'M1' and data['entered_in'] != 'M2':
        db_session.rollback()
        return ERRORS.UNEXPECTED_INPUT_VALUE
      
      student.entree_en_m1 = data['entered_in'] == 'M1'
    if 'graduated' in data and type(data['graduated']) == bool:
      student.diplome = data['graduated']

    # Save changes
    db_session.commit()
    
    return flask.jsonify(student)

  @app.route('/student/confirm')
  @login_required
  def confirm_actual_data_student():
    student: Etudiant = get_student_or_none()

    if not student:
      return ERRORS.STUDENT_NOT_FOUND

    student.refresh_update()
    db_session.commit()

    return flask.jsonify(student)


  @app.route('/student/<int:id>', methods=["DELETE"])
  @login_required
  def delete_student(id: int):
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    # Check if exists
    etu = Etudiant.query.filter_by(id_etu=id).one_or_none()

    if not etu:
      return ""

    Etudiant.query.filter_by(id_etu=id).delete()
    # delete cascade does not work??
    Token.query.filter_by(id_etu=id).delete()

    db_session.commit()

    return ""

  
  @app.route('/student/mail', methods=["POST"])
  @login_required
  def send_mails():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    r = get_request()

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'content', 'to', 'object'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    content, to, obj = data['content'], data['to'], data['object']

    # If $to is not a list, or $to is a empty list, or some $to elements are not strings
    if type(to) is not list or len(to) == 0 or any(map(lambda x: type(x) is not str, to)):
      return ERRORS.INVALID_INPUT_TYPE

    # Send the mail...
    send_basic_mail(content, to, obj)

    return ""

  @app.route('/student/lost_token')
  def lost_token():
    r = get_request()

    if not 'email' in r.args or type(r.args['email']) is not str:
      return ERRORS.BAD_REQUEST

    email = r.args['email']

    st: Etudiant = Etudiant.query.filter_by(mail=email).one_or_none()

    if not st:
      return ERRORS.STUDENT_NOT_FOUND

    send_welcome_mail(st.id_etu)
    return ""

  @app.route('/student/ask_refresh', methods=["POST"])
  @login_required
  def ask_refresh():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    r = get_request()
    data = r.json

    if not 'ids' in data or type(data['ids']) is not list:
      return ERRORS.BAD_REQUEST


    for id_etu in data['ids']:
      st: Etudiant = Etudiant.query.filter_by(id_etu=id_etu).one_or_none()

      if not st:
        return ERRORS.STUDENT_NOT_FOUND

      send_ask_relogin_mail(st.id_etu)

    return ""

  @app.route('/student/in')
  @login_required
  def fetch_student_of_location():
    r = get_request()

    cmps: List[Entreprise] = []
    if 'town' in r.args:
      cmps = Entreprise.query.filter_by(ville=r.args['town']).all()

    jobs_etudiants: Dict[Etudiant, List[Emploi]] = {}
    stages_etudiants: Dict[Etudiant, List[Stage]] = {}

    for c in cmps:
      emplois_realises: List[Emploi] = Emploi.query.filter_by(id_entreprise=c.id_entreprise).all()
      for emploi in emplois_realises:
        etu: Etudiant = emploi.etudiant
        if etu in jobs_etudiants:
          jobs_etudiants[etu].append(emploi)
        else:
          jobs_etudiants[etu] = [emploi]

      stages_realises: List[Stage] = Stage.query.filter_by(id_entreprise=c.id_entreprise).all()
      for stage in stages_realises:
        etu: Etudiant = stage.etudiant
        if etu in stages_etudiants:
          stages_etudiants[etu].append(stage)
        else:
          stages_etudiants[etu] = [stage]

    # On a récup tous les emplois/stages par étudiant
    # On créé des objets partiels
    # Liste de {
    #   'student': {'name': str, 'surname': str, 'mail': str}, 
    #   'type': 'internship'|'job', 
    #   'ended': bool,
    #   'related_date': string,
    #   'company': str
    # }
    # On skip les étudiants qui ne veulent pas être visibles
    available = []

    for student, emplois in jobs_etudiants.items():
      if not student.visible:
        continue

      companies_for_student = set()

      for emploi in emplois:
        if emploi.entreprise.nom in companies_for_student:
          continue

        companies_for_student.add(emploi.entreprise.nom)
        ended = emploi.fin != None
        related = str(emploi.debut)

        if ended:
          related = str(emploi.fin)

        available.append({
          'ended': ended,
          'student': {
            'name': student.nom,
            'surname': student.prenom,
            'mail': student.mail
          },
          'related_date': related,
          'type': 'job',
          'company': emploi.entreprise.nom
        })

    for student, stages in stages_etudiants.items():
      if not student.visible:
        continue

      companies_for_student = set()

      for stage in stages:
        if stage.entreprise.nom in companies_for_student:
          continue

        companies_for_student.add(stage.entreprise.nom)

        available.append({
          'ended': True,
          'student': {
            'name': student.nom,
            'surname': student.prenom,
            'mail': student.mail
          },
          'type': 'internship',
          'related_date': stage.promo,
          'company': stage.entreprise.nom
        })

    return flask.jsonify(available)

