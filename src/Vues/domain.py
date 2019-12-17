import flask
from Models.Domaine import Domaine
from Models.Emploi import Emploi
from Models.Stage import Stage
from flask_login import login_required
from models_helpers import get_student_or_none
from helpers import is_teacher, get_request, get_user, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict

def define_domain_endpoints(app: flask.Flask):
  @app.route('/domain/create', methods=["POST"])
  @login_required
  def make_domain():
    r = get_request()
    
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'domain', 'name'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    domain, nom = data['domain'], data['name']

    ## Search for similar domains TODO improve search
    f = Domaine.query.filter(Domaine.domaine.ilike(f"{domain}")).all()

    if len(f):
      return flask.jsonify(f[0]), 200

    # Create new domain
    dom = Domaine.create(domaine=domain, nom=nom)
    db_session.add(dom)
    db_session.commit()

    return flask.jsonify(dom), 201

  @app.route('/domain/modify', methods=["POST"])
  @login_required
  def modify_domain():
    r = get_request()
    
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'domain', 'name', 'id'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    domain, nom, id_domaine = data['domain'], data['name'], data['id']

    if type(id_domaine) is not int:
      print("Bad id")
      return ERRORS.BAD_REQUEST

    d: Domaine = Domaine.query.filter_by(id_domaine=id_domaine).one_or_none()

    if not d:
      return ERRORS.DOMAIN_NOT_FOUND

    if d.domaine == "other":
      return ERRORS.BAD_REQUEST

    search = Domaine.query.filter_by(domaine=domain).one_or_none()
    if search and d.domaine != search.domaine:
      # TODO message CLIENT error already exists
      return ERRORS.DOMAIN_ALREADY_EXISTS

    d.nom = nom
    d.domaine = domain

    # Refresh
    db_session.commit()

    return flask.jsonify(d)



  @app.route('/domain/<int:id>', methods=["DELETE"])
  @login_required
  def delete_domain(id: int):
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    d: Domaine = Domaine.query.filter_by(id_domaine=id).one_or_none()

    if not d:
      return ""

    other_domain: Domaine = Domaine.query.filter_by(domaine="other").one_or_none()
    domain_id = None

    if other_domain:
      domain_id = other_domain.id_domaine

      if other_domain.id_domaine == id:

        return ERRORS.BAD_REQUEST

    Stage.query.filter_by(id_domaine=id).update({"id_domaine": domain_id})
    Emploi.query.filter_by(id_domaine=id).update({"id_domaine": domain_id})

    db_session.delete(d)
    db_session.commit()

    return ""


  @app.route('/domain/all')
  def fetch_domains():
    return flask.jsonify(Domaine.query.all())


  @app.route('/domain/merge', methods=["POST"])
  @login_required
  def merge_domains():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    r = get_request()

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'main', 'children'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    main, children = data['main'], data['children']

    if type(main) is not int or type(children) is not list:
      return ERRORS.BAD_REQUEST

    main_domaine: Domaine = Domaine.query.filter_by(id_domaine=main).one_or_none()

    if not main_domaine:
      return ERRORS.DOMAIN_NOT_FOUND

    children_domains: List[Domaine] = []
    for c in children:
      if type(c) is not int:
        return ERRORS.BAD_REQUEST

      ent = Domaine.query.filter_by(id_domaine=c).one_or_none()
      if not ent:
        return ERRORS.DOMAIN_NOT_FOUND

      children_domains.append(ent)

    # For each domain relied to children_domains, set main_domaine
    for c in children_domains:
      Stage.query.filter_by(id_domaine=c.id_domaine).update({'id_domaine': main_domaine.id_domaine})
      Emploi.query.filter_by(id_domaine=c.id_domaine).update({'id_domaine': main_domaine.id_domaine})

    # Delete every children domain
    for c in children_formations:
      db_session.delete(c)

    db_session.commit()
    return ""

