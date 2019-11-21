import flask
from Models.Entreprise import Entreprise
from Models.Contact import Contact
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict
from sqlalchemy import and_, or_


def define_contact_endpoints(app: flask.Flask):
  @app.route('/contact/create', methods=["POST"])
  @login_required
  def make_contact():
    r = get_request()
    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'mail', 'id_entreprise'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    name, mail, id_entreprise = data['name'], data['mail'], data['id_entreprise']

    ## Search for similar contact TODO improve search
    f = Contact.query.filter(and_(Contact.nom.ilike(f"{name}"), Contact.mail.ilike(f"{mail}"),
                                  Contact.id_entreprise.ilike(f"{entreprise}"))).all()
      
    if len(f):
      attach_previous_contact(user_id, f[0].id_entreprise)
      return flask.jsonify(f[0]), 200

    #Check id_entreprise
    ent: Entreprise = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()

    if not ent:
      ERRORS.BAD_REQUEST
    

    email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
    if not re.match(email_catch, email):
      return ERRORS.BAD_REQUEST

    # Create new contact
    cont = Contact.create(nom=name, mail=mail, id_entreprise=id_entreprise)
    db_session.add(cont)
    db_session.commit()

    return flask.jsonify(cont), 201

  @app.route('/contact/all')
  @login_required
  def fetch_contact():
    r = get_request()

    id_e = None
    if 'company' in r.args:
      try:
        id_e = int(r.args['company'])
      except:
        pass
      
    if not id_e or id_e < 0:
      return ERRORS.MISSING_PARAMETERS

    return flask.jsonify(Contact.query.filter_by(id_entreprise=id_e).all())


  @app.route('/contact/related')
  @login_required
  def find_relative_contact():
    r = get_request()
    name: str = None
    mail: str = None
    id_entreprise: int = None
    included = False

    if 'name' in r.args:
      name = r.args['name']
    if 'mail' in r.args:
      mail = r.args['mail']
    if 'id_entreprise' in r.args:
        id_entreprise = r.args['id_entreprise']
    if 'included' in r.args and is_truthy(r.args['included']):
      included = True

    # get all contacts
    contacts: List[Contact] = Contact.query.all()

    accepted: List[Tuple[Contact, Dict[str, float]]] = []

    # Find contacts that matches the query
    for f in contacts:
      dist_name = 0
      dist_mail = 0
      if name:
        dist_name = Levenshtein.ratio(f.nom, name)
      if mail:  
        dist_mail = Levenshtein.ratio(f.mail, mail)

      if dist_name >= 0.6 or dist_mail >= 0.6:
        accepted.append((f, {'name': dist_name, 'location': dist_mail}))
        continue
      
      # Search for substrings
      if included:
        if name and name in f.nom:
          accepted.append((f, {'name': dist_name, 'location': dist_mail}))
        elif mail and location in f.mail:
          accepted.append((f, {'name': dist_name, 'location': dist_mail}))

    # Sort the accepted by max between dist_name and dist_location
    accepted.sort(key=lambda x: max((x[1]['name'], x[1]['mail'])), reverse=True)

    return flask.jsonify(accepted)
