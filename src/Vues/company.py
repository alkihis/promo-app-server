import flask
from flask_login import login_required
from Models.Entreprise import Entreprise
from helpers import is_teacher, get_request, get_user, create_token_for, convert_date
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict
from sqlalchemy import and_, or_

def define_company_endpoints(app: flask.Flask):
  @app.route('/company/create', methods=["POST"])
  @login_required
  def make_entreprise():
    r = get_request()
    user_id = r.args.get('user_id', None)

    if not is_teacher():
      user_id = get_user().id_etu

    if not user_id or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'city', 'size', 'status'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

      name, city, size, status = data['name'], data['city'], data['size'], data['status']

      ## Search for similar company TODO improve search
      f = Entreprise.query.filter(and_(Entreprise.nom.ilike(f"{name}"), Entreprise.ville.ilike(f"{city}"))).all()
      
      if len(f):
        return flask.jsonify(f[0]), 200

    # Create new company
    comp = Entreprise.create(nom=name, ville=city, taille=size, statut=status )
    db_session.add(comp)
    db_session.commit()

    #attach_previous_contact(user_id, cont.id_entreprise)

    return flask.jsonify(comp), 201

  @app.route('/company/all')
  @login_required
  def fetch_company():
    return flask.jsonify(Entreprise.query.all())

  @app.route('/company/related')
  @login_required
  def find_relative_company():
    r = get_request()
    name: str = None
    city: str = None
    included = False

    if 'name' in r.args:
      name = r.args['name']
    if 'city' in r.args:
      ville = r.args['city']
    if 'included' in r.args and is_truthy(r.args['included']):
      included = True

    # get all company
    company: List[Company] = Company.query.all()

    accepted: List[Tuple[Entreprise, Dict[str, float]]] = []

    # Find contacts that matches the query
    for f in contacts:
      dist_name = 0
      dist_city = 0
      if name:
        dist_name = Levenshtein.ratio(f.nom, name)
      if city:  
        dist_city = Levenshtein.ratio(f.ville, city)

      if dist_name >= 0.6 or dist_city >= 0.6:
        accepted.append((f, {'name': dist_name, 'city': dist_city}))
        continue
      
      # Search for substrings
      if included:
        if name and name in f.nom:
          accepted.append((f, {'name': dist_name, 'city': dist_city}))
        elif city and city in f.city:
          accepted.append((f, {'name': dist_name, 'city': dist_city}))

    # Sort the accepted by max between dist_name and dist_location
    accepted.sort(key=lambda x: max((x[1]['name'], x[1]['city'])), reverse=True)

    return flask.jsonify(accepted)