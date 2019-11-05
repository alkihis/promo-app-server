import flask
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict


def define_emploi_endpoints(app: flask.Flask):
  @app.route('/emploi/create', methods=["POST"])
  @login_required
  def make_emploi():
    r = get_request()
    user_id = r.args.get('user_id', None)

    if not is_teacher():
      user_id = get_user().id_etu

    if not user_id or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    ########### TODO: check parametres emplois

    if not {'start', 'end', 'contract', 'salary', 'is_public', 'level'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    start, end, contract, salary, is_public, level = data['start'], data['end'], data['contract'], data['salary'], data['is_public'], data['level']


    # Create new emploi
    emp = Emploi.create(debut=start, fin=end, contrat=contract id_entreprise=id_entreprise, id_domaine=id_domain, id_contact=id_contact, id_etu=user_id, salaire=salary)
    db_session.add(emp)
    db_session.commit()

    # attach_previous_emploi(user_id, emp.id_emp)

    return flask.jsonify(emp), 201


  @app.route('/emploi/all')
  @login_required
  def fetch_locations():
    return flask.jsonify(Emploi.query.all())

# def attach_previous_formation(id_etu: int, id_form: int):
#   e: Etudiant = Etudiant.query.filter_by(id_etu=id_etu).one_or_none()

#   if e:
#     e.cursus_anterieur = id_form
#     db_session.commit()