import flask
from Models.Etudiant import Etudiant
from Models.Formation import Formation
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, convert_date, is_truthy
from errors import ERRORS
from server import db_session
from sqlalchemy import and_
import Levenshtein
from typing import List, Tuple, Dict
from models_helpers import get_student_or_none

def define_formation_endpoints(app: flask.Flask):
  @app.route('/formation/create', methods=["POST"])
  @login_required
  def create_formation():
    r = get_request()
    stu: Etudiant = get_student_or_none()

    if not stu or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'location', 'level'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    branch, location, level = data['name'], data['location'], data['level']

    # TODO check level: must be in ENUM
    if type(level) is not str:
      return ERRORS.BAD_REQUEST
    
    valid_levels = {"licence", "master", "phd", "other"}
    if level not in valid_levels:
      return ERRORS.BAD_REQUEST


    ## Search for similar formations TODO improve search
    f = Formation.query.filter(and_(Formation.filiere.ilike(f"{branch}"), Formation.lieu.ilike(f"{location}"), Formation.niveau.ilike(f"{level}"))).all()

    if len(f):
      return flask.jsonify(f[0])

    # Create new formation
    form = Formation.create(filiere=branch, lieu=location, niveau=level)
    db_session.add(form)
    db_session.commit()

    return flask.jsonify(form), 201


  @app.route('/formation/all')
  @login_required
  def fetch_locations():
    return flask.jsonify(Formation.query.all())


  @app.route('/formation/<int:id>', methods=["DELETE"])
  @login_required
  def delete_formation(id: int):
    # Get logged etudiant
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    form: Formation = Formation.query.filter_by(id_formation=id).one_or_none()

    if not form:
      return ""

    # Supprime les formations des étudiants
    for etu in Etudiant.query.filter_by(cursus_anterieur=id).all():
      etu.cursus_anterieur = None

    for etu in Etudiant.query.filter_by(reorientation=id).all():
      e.reorientation = None
  
    db_session.commit()

    return ""


  @app.route('/formation/related')
  @login_required
  def find_relative_locations():
    r = get_request()
    name: str = None
    location: str = None
    included = False

    if 'name' in r.args:
      name = r.args['name']
    if 'location' in r.args:
      location = r.args['location']
    if 'included' in r.args and is_truthy(r.args['included']):
      included = True

    # get all formations
    formations: List[Formation] = Formation.query.all()

    accepted: List[Tuple[Formation, Dict[str, float]]] = []

    # Find formations that matches the query
    for f in formations:
      dist_name = 0
      dist_location = 0
      if name:
        dist_name = Levenshtein.ratio(f.nom, name)
      if location:  
        dist_location = Levenshtein.ratio(f.lieu, location)

      if dist_name >= 0.6 or dist_location >= 0.6:
        accepted.append((f, {'name': dist_name, 'location': dist_location}))
        continue
      
      # Search for substrings
      if included:
        if name and name in f.nom:
          accepted.append((f, {'name': dist_name, 'location': dist_location}))
        elif location and location in f.lieu:
          accepted.append((f, {'name': dist_name, 'location': dist_location}))

    # Sort the accepted by max between dist_name and dist_location
    accepted.sort(key=lambda x: max((x[1]['name'], x[1]['location'])), reverse=True)

    return flask.jsonify(accepted)

