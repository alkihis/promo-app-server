import flask
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant
from Models.Stage import Stage
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict


def define_internship_endpoints(app: flask.Flask):
  @app.route('/intrenship/create', methods=["POST"])
  @login_required
  def make_internship():
    r = get_request()
    user_id = r.args.get('user_id', None)

    if not is_teacher():
      user_id = get_user().id_etu

    if not user_id or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    ########### TODO: check parametres internships

    if not {'promo_year', 'id_entreprise', 'domain', 'id_contact'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    promo_year, id_entreprise, domain, id_contact = data['promo_year'], data['id_entreprise'], data['domain'], data['id_contact']

    ## Check company id
    ent: Entreprise = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()

    if not ent:
        return ERRORS.BAD_REQUEST


    ##  Domain to id
    dom: Domaine = Domaine.query.filter_by(domaine=domain).one_or_none()

    if not dom:
        return ERRORS.BAD_REQUEST
    
    id_domain = dom.id_domaine


    ## Check contact id
    cont: Contact = Contact.query.filter_by(id_contact=id_contact).one_or_none()

    if not cont:
        return ERRORS.BAD_REQUEST

    # Create new internship
    inter = Stage.create(promo=promo_year, id_entreprise=id_entreprise, id_domaine=id_domain, id_contact=id_contact, id_etu=user_id)
    db_session.add(inter)
    db_session.commit()

    return flask.jsonify(inter), 201


  @app.route('/internship/all')
  @login_required
  def fetch_internships():
    return flask.jsonify(Stage.query.all())
