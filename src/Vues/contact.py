import flask
from Models.Entreprise import Entreprise
from Models.Emploi import Emploi
from Models.Stage import Stage
from Models.Contact import Contact
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict
from sqlalchemy import and_, or_
import re

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
    f = Contact.query.filter(
      and_(
        Contact.nom.ilike(f"{name}"), 
        Contact.mail.ilike(f"{mail}"), 
        Contact.id_entreprise.ilike(f"{id_entreprise}")
      )
    ).all()
      
    if len(f):
      return flask.jsonify(f[0]), 200

    #Check id_entreprise
    ent: Entreprise = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()

    if not ent:
      ERRORS.BAD_REQUEST
    

    email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
    if not re.match(email_catch, mail):
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


  @app.route('/contact/in')
  @login_required
  def fetch_contact_of_location():
    r = get_request()

    cmps: List[Entreprise] = []
    if 'town' in r.args:
      cmps = Entreprise.query.filter_by(ville=r.args['town']).all()

    contacts: List[Contact] = []

    for c in cmps:
      contacts_of_cmp = Contact.query.filter_by(id_entreprise=c.id_entreprise).all()

      for contact in contacts_of_cmp:
        contacts.append(contact)

    return flask.jsonify([contact.to_json(full=True) for contact in contacts])
    

  @app.route('/contact/modify', methods=["POST"])
  @login_required
  def modify_contact():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    r = get_request()
    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'mail', 'id'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    name, mail, id_contact = data['name'], data['mail'], data['id']

    if type(id_contact) is not int:
      return ERRORS.BAD_REQUEST

    c: Contact = Contact.query.filter_by(id_contact=id_contact).one_or_none()

    if not c:
      return ERRORS.RESOURCE_NOT_FOUND
    

    email_catch = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$" 
    if not re.match(email_catch, mail):
      return ERRORS.BAD_REQUEST

    # Create new contact
    c.mail = mail
    c.nom = name
    db_session.commit()

    return flask.jsonify(c)


  @app.route('/contact/<int:id>', methods=["DELETE"])
  @login_required
  def delete_contact(id: int):
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    c = Contact.query.filter_by(id_contact=id).one_or_none()

    if not c:
      return ""

    Emploi.query.filter_by(id_contact=id).update({"id_contact": None})
    Stage.query.filter_by(id_contact=id).update({"id_contact": None})

    db_session.delete(c)
    db_session.commit()

    return ""

