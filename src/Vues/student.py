import flask
from Models.Etudiant import Etudiant
from Models.Formation import Formation
from flask_login import login_required
from helpers import is_teacher, get_request, create_token_for, convert_date
from errors import ERRORS
from server import db_session
from sqlalchemy import and_, or_
### Vues pour l'API /student

def student_routes(app: flask.Flask):
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
    # Required are first_name, last_name, email, promo_in, birthdate 
    data = r.json

    # Si toutes ces clés ne sont pas présentes dans le dict
    if not {'first_name', 'last_name', 'email', 'promo_in', 'birthdate'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    first_name, last_name, email = data['first_name'], data['last_name'], data['email']
    promo_in, birthdate = data['promo_in'], data['birthdate']

    # Do not forget to change datestring to date object !
    birthdate = convert_date(birthdate)

    ## TODO CHECK PROMO, CHECK EMAIL VALIDITY

    # Create student
    etu = Etudiant.create(nom=last_name, prenom=first_name, mail=email, birthdate=birthdate, promo_entree=promo_in)

    db_session.add(etu)
    db_session.commit()

    # Create a token automatically
    create_token_for(etu.id_etu, teacher=False)

    # Return the newly created student
    return flask.jsonify(etu)

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
    # name, promo_in, promo_out, previous_formation

    arguments_for_search = []

    # Constructing search
    if 'name' in r.args:
      arguments_for_search.append(or_(Etudiant.nom.ilike('%' + r.args['name'] + '%'), Etudiant.prenom.ilike('%' + r.args['name'] + '%')))
    if 'promo_in' in r.args:
      arguments_for_search.append(Etudiant.promo_entree == r.args['promo_in'])
    if 'promo_out' in r.args:
      arguments_for_search.append(Etudiant.promo_sortie == r.args['promo_out'])
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

