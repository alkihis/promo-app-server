import flask
from Models.Domaine import Domaine
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict

def define_domain_endpoints(app: flask.Flask):
  @app.route('/domain/create', methods=["POST"])
  @login_required
  def make_domain():
    r = get_request()
    user_id = r.args.get('user_id', None)

    if not is_teacher():
      user_id = get_user().id_etu

    if not user_id or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'domain'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    domain = data['domain']

    ## Search for similar domains TODO improve search
    f = Domaine.query.filter(Domaine.domaine.ilike(f"{domain}")).all()

    if len(f):
      return flask.jsonify(f[0]), 200

    # Create new domain
    dom = Domaine.create(domain=domain)
    db_session.add(dom)
    db_session.commit()

    #attach_previous_domain(user_id, dom.id_dom)

    return flask.jsonify(dom), 201


  @app.route('/domain/all')
  @login_required
  def fetch_domains():
    return flask.jsonify(Domaine.query.all())
