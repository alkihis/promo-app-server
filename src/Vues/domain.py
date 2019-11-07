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
      attach_previous_domain(user_id, f[0].id_dom)
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

  @app.route('/domain/related')
  @login_required
  def find_relative_domains():
    r = get_request()
    domain: str = None
    included = False

    if 'domain' in r.args:
      domain = r.args['domain']
    if 'included' in r.args and is_truthy(r.args['included']):
      included = True

    # get all domains
    domains: List[Domaine] = Domaine.query.all()

    accepted: List[Tuple[Domaine, Dict[str, float]]] = []

    # Find domains that matches the query
    for f in domains:
      dist_domain = 0
      if domain:
        dist_domain = Levenshtein.ratio(f.domaine, domain)
      
      # Search for substrings
      if included:
        if domain and domain in f.nom:
          accepted.append((f, {'domain': dist_domain}))

    # Sort the accepted by max between dist_domain and dist_location
    accepted.sort(key=lambda x: max((x[1]['domain'])), reverse=True)

    return flask.jsonify(accepted)
