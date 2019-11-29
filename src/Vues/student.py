import flask
from Models.Etudiant import Etudiant
from Models.Formation import Formation
from Models.Token import Token
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, create_token_for, convert_date, is_truthy
from models_helpers import get_student_or_none, send_basic_mail, create_a_student
from errors import ERRORS
from server import db_session, engine
from sqlalchemy import and_, or_
import datetime
import re
from typing import List
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
      return ERRORS.RESOURCE_NOT_FOUND

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
    student: Etudiant = get_student_or_none()

    if not student or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if 'first_name' in data:
      # TODO Check validity
      special_check = r"^[A-Za-z-_ ]+$" 
      if not re.match(special_check,data['first_name']):
        return ERRORS.BAD_REQUEST

      student.prenom = data['first_name']

    if 'last_name' in data:
      # TODO Check validity
      special_check = r"^[A-Za-z-_ ]+$" 
      if not re.match(special_check,data['last_name']):
        return ERRORS.BAD_REQUEST

      student.nom = data['last_name']

    if 'year_in' and 'year_out' in data:
      # TODO Check validity
      try:
        year_in = int(data['year_in'])
      except:
        ERRORS.BAD_REQUEST
      
      try:
        year_out = int(data['year_out'])
      except:
        ERRORS.BAD_REQUEST
                  
      if year_in > year_out:
        ERRORS.BAD_REQUEST

      student.annee_entree = data['year_in']
      student.annee_sortie = data['year_out']


    elif 'year_in' in data:
      try:
        year_in = int(data['year_in'])
      except:
        ERRORS.BAD_REQUEST

      if year_in >= student.annee_sortie:
        return ERRORS.BAD_REQUEST
      
      student.annee_entree = data['year_in']

    elif 'year_out' in data:
      # TODO Check validity
      try:
          year_out = int(data['year_out'])
      except:
        ERRORS.BAD_REQUEST

      if student.annee_entree >= year_out:
        return ERRORS.BAD_REQUEST

      student.annee_sortie = data['year_out']

    if 'email' in data:
      # TODO Check validity
      email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
      if not re.match(email_catch, data['email']):
        return ERRORS.BAD_REQUEST

      student.mail = data['email']
      
    if 'previous_formation' in data:
      if type(data['previous_formation']) == int:
        # Check existance of formation
        desired = Formation.query.filter_by(id_form=data['previous_formation']).one_or_none()

        if desired:
          student.cursus_anterieur = data['previous_formation']
        else:
          db_session.rollback()
          return ERRORS.RESOURCE_NOT_FOUND
      elif data['previous_formation'] is None:
        student.cursus_anterieur = None
      else:
        db_session.rollback()
        return ERRORS.BAD_REQUEST
    if 'next_formation' in data:
      if type(data['next_formation']) == int:
        # Check existance of formation
        desired = Formation.query.filter_by(id_form=data['next_formation']).one_or_none()

        if desired:
          student.reorientation = data['next_formation']
        else:
          db_session.rollback()
          return ERRORS.RESOURCE_NOT_FOUND
      elif data['next_formation'] is None:
        student.reorientation = None
      else:
        db_session.rollback()
        return ERRORS.BAD_REQUEST
    if 'entered_in' in data:
      if data['entered_in'] != 'M1' and data['entered_in'] != 'M2':
        db_session.rollback()
        return ERRORS.BAD_REQUEST
      
      student.entree_en_m1 = data['entered_in'] == 'M1'
    if 'graduated' in data and type(data['graduated']) == bool:
      student.diplome = data['graduated']

    # Save changes
    db_session.commit()

    print(student.to_json())
    
    return flask.jsonify(student)


  @app.route('/student/search')
  @login_required
  def search_students():
    # Define search pages and page length
    page = 0
    length = 20
    r = get_request()

    if r.args.get('page') is not None:
      try:
        choosen_page = int(r.args.get('page'))

        if choosen_page >= 0:
          page = choosen_page
      except:
        return ERRORS.BAD_REQUEST

    if r.args.get('count') is not None:
      try:
        choosen_count = int(r.args.get('count'))

        if choosen_count > 0 and choosen_count <= 100:
          length = choosen_count
      except:
        return ERRORS.BAD_REQUEST

    # Search for search parameters in request
    # name, year_in, year_out, previous_formation

    arguments_for_search = []

    # Constructing search
    if 'name' in r.args:
      arguments_for_search.append(or_(Etudiant.nom.ilike('%' + r.args['name'] + '%'), Etudiant.prenom.ilike('%' + r.args['name'] + '%')))
    if 'year_in' in r.args:
      arguments_for_search.append(Etudiant.annee_entree == r.args['year_in'])
    if 'year_out' in r.args:
      arguments_for_search.append(Etudiant.annee_sortie == r.args['year_out'])
    if 'previous_formation' in r.args:
      arguments_for_search.append(
        and_(
          Etudiant.cursus_anterieur != None, 
          Formation.nom.ilike('%' + r.args['previous_formation'] + '%'),
          Etudiant.cursus_anterieur == Formation.id_form
        )
      )

    # Make the search
    results = Etudiant.query.filter(and_(*arguments_for_search)).all()

    return flask.jsonify(results)


  @app.route('/student/confirm')
  @login_required
  def confirm_actual_data_student():
    student: Etudiant = get_student_or_none()

    if not student:
      return ERRORS.BAD_REQUEST

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
      print("Addresses must be a list of string")
      return ERRORS.BAD_REQUEST

    # Send the mail...
    send_basic_mail(content, to, obj)

    return ""

  @app.route('/student/lost_token')
  def lost_token():
    r = get_request()

    if not 'email' in r.args or type(r.args['email']) is not str:
      return ERRORS.BAD_REQUEST

    email = r.args['email']

    tk: Token = Token.query.join(Etudiant).filter_by(mail=email).all()

    if len(tk):
      ## TODO send email with token to student
      # URL: http://<site-url>/login?token={tk.token}
      pass

    # Generate a token
    st: Etudiant = Etudiant.query.filter_by(mail=email).one_or_none()

    if not st:
      return ERRORS.RESOURCE_NOT_FOUND

    tk = create_token_for(st.id_etu, False)

    ## TODO send email with token to student
    # URL: http://<site-url>/login?token={tk.token}

