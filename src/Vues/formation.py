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

def define_formation_endpoints(app: flask.Flask):
  @app.route('/formation/create', methods=["POST"])
  @login_required
  def make_formation():
    r = get_request()
    user_id = r.args.get('user_id', None)

    if not is_teacher():
      user_id = get_user().id_etu

    if not user_id or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'location'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    name, location = data['name'], data['location']

    ## Search for similar formations TODO improve search
    f = Formation.query.filter(and_(Formation.nom.ilike(f"{name}"), Formation.lieu.ilike(f"{location}"))).all()

    if len(f):
      attach_previous_formation(user_id, f[0].id_form)
      return flask.jsonify(f[0]), 200

    # Create new formation
    form = Formation.create(nom=name, lieu=location)
    db_session.add(form)
    db_session.commit()

    attach_previous_formation(user_id, form.id_form)

    return flask.jsonify(form), 201


  @app.route('/formation/all')
  @login_required
  def fetch_locations():
    return flask.jsonify(Formation.query.all())

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

def attach_previous_formation(id_etu: int, id_form: int):
  e: Etudiant = Etudiant.query.filter_by(id_etu=id_etu).one_or_none()

  if e:
    e.cursus_anterieur = id_form
    db_session.commit()

