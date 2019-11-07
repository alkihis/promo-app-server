import flask
from Models.Etudiant import Etudiant
from Models.Formation import Formation
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, create_token_for, convert_date
from errors import ERRORS
from server import db_session
from sqlalchemy import and_, or_
import datetime
import re
### Vues pour l'API /student

def student_routes(app: flask.Flask):
  # Get logged student
  @app.route('/student/self')
  @login_required
  def get_self_logged():
    if is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    currently_logged = get_user().id_etu
    return get_id(currently_logged)

  # Get a single Etudiant by ID
  @app.route('/student/<int:id>')
  def get_id(id: int):
    e: Etudiant = Etudiant.query.filter_by(id_etu=identifier).one_or_none()

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

    # Si toutes ces clés ne sont pas présentes dans le dict
    if not {'first_name', 'last_name', 'email', 'year_in', 'entered_in'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    first_name, last_name, email = data['first_name'], data['last_name'], data['email']
    year_in, entree = data['year_in'], data['entered_in']

    # Do not forget to change datestring to date object !
    # birthdate = convert_date(birthdate)

    ## TODO CHECK PROMO, CHECK EMAIL VALIDITY
    student_check = Etudiant.query.filter_by(mail=email).one_or_none()
    if student_check:
      return ERRORS.CONFLICT

    email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
    res = re.match(email,email_catch)
    if res == None:
      return ERRORS.CONFLICT


    current_date = datetime.datetime.now().date().year()

    if int(year_in) > current_date or int(year_in) <= 2015:
      return ERRORS.CONFLICT
    
    # Create student
    etu = Etudiant.create(nom=last_name, prenom=first_name, mail=email, annee_entree=year_in, entree_en_m1=entree == "M1")

    db_session.add(etu)
    db_session.commit()

    # Create a token automatically
    create_token_for(etu.id_etu, teacher=False)

    # Return the newly created student
    return flask.jsonify(etu)


  @app.route('/student/update', methods=['POST'])
  @login_required
  def update_student():
    r = get_request()
    student: Etudiant = None

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    if is_teacher():
      if 'user_id' in r.args:
        user_id = int(r.args['user_id'])
        st = Etudiant.query.filter_by(id_etu=user_id).one_or_none()

        if st:
          student = st
        else:
          return ERRORS.RESOURCE_NOT_FOUND
      else:
        return ERRORS.MISSING_PARAMETERS
    else:
      student = Etudiant.query.filter_by(id_etu=get_user().id_etu).first()

    data = r.json

    if 'first_name' in data:
      # TODO Check validity
      student.prenom = data['first_name']
    if 'last_name' in data:
      # Check validity
      student.nom = data['last_name']
    if 'year_in' in data:
      # Check validity
      student.annee_entree = data['year_in']
    if 'year_out' in data:
      student.annee_sortie = data['year_out']
    if 'email' in data:
      student.mail = data['email']
    if 'previous_formation' in data:
      if type(data['previous_formation']) == int:
        # Check existance of formation
        desired = Formation.query.filter_by(id_form=data['previous_formation']).one_or_none()

        if desired:
          student.cursus_anterieur = data['previous_formation']
        else:
          return ERRORS.RESOURCE_NOT_FOUND
      elif data['previous_formation'] is None:
        student.cursus_anterieur = None
      else:
        return ERRORS.BAD_REQUEST
    if 'next_formation' in data:
      if type(data['next_formation']) == int:
        # Check existance of formation
        desired = Formation.query.filter_by(id_form=data['next_formation']).one_or_none()

        if desired:
          student.reorientation = data['next_formation']
        else:
          return ERRORS.RESOURCE_NOT_FOUND
      elif data['next_formation'] is None:
        student.reorientation = None
      else:
        return ERRORS.BAD_REQUEST

    # Save changes
    db_session.commit()
    
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

