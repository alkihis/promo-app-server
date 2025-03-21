import flask
from flask_login import login_required
from Models.Entreprise import Entreprise
from Models.Contact import Contact
from Models.Emploi import Emploi
from Models.Stage import Stage
from helpers import is_teacher, get_request, get_user, create_token_for, convert_date, is_truthy
from models_helpers import get_student_or_none, get_location_of_company
from errors import ERRORS
from server import db_session, engine
from typing import List, Tuple, Dict
from sqlalchemy import and_, or_
import re

def define_company_endpoints(app: flask.Flask):
  @app.route('/company/create', methods=["POST"])
  @login_required
  def make_entreprise():
    r = get_request()
    stu = get_student_or_none()

    if not stu or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'city', 'size', 'status'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    name, city, size, status = data['name'], data['city'], data['size'], data['status']

    ## Search for similar company
    f = Entreprise.query.filter(and_(Entreprise.nom.ilike(f"{name}"), Entreprise.ville.ilike(f"{city}"))).all()
    
    if len(f):
      return flask.jsonify(f[0])
    
    if type(name) is not str:
      return ERRORS.INVALID_INPUT_TYPE

    special_check = r"^[\w_ -]+$" 
    if not re.match(special_check, name):
      return ERRORS.INVALID_INPUT_VALUE

    # Checks for size and status (enum voir TS interfaces.ts)
    if type(size) is not str:
      return ERRORS.INVALID_INPUT_TYPE

    valid_comp_size = {"small", "big", "medium", "very_big"}
    if size not in valid_comp_size:
      return ERRORS.UNEXPECTED_INPUT_VALUE

    # Checks for status (enum voir TS interfaces.ts)
    if type(status) is not str:
      return ERRORS.INVALID_INPUT_TYPE

    valid_comp_status = {"public", "private"}
    if status not in valid_comp_status:
      return ERRORS.UNEXPECTED_INPUT_VALUE

    gps_coords = get_location_of_company(city)

    # Create new company
    comp = Entreprise.create(nom=name, ville=city, taille=size, statut=status, lat=gps_coords[0], lng=gps_coords[1])
    db_session.add(comp)
    db_session.commit()

    return flask.jsonify(comp), 201


  @app.route('/company/modify', methods=["POST"])
  @login_required
  def modify_entreprise():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    r = get_request()

    if not r.is_json:
      return ERRORS.INVALID_INPUT_TYPE

    data = r.json

    if not {'name', 'town', 'size', 'status', 'id'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    if type(data['id']) is not int:
      return ERRORS.INVALID_INPUT_TYPE

    e: Entreprise = Entreprise.query.filter_by(id_entreprise=int(data['id'])).one_or_none()

    if not e:
      return ERRORS.COMPANY_NOT_FOUND

    name, city, size, status = data['name'], data['town'], data['size'], data['status']

    if type(name) is not str:
      return ERRORS.INVALID_INPUT_TYPE
    
    special_check = r"^[\w_ -]+$" 
    if not re.match(special_check, name):
      return ERRORS.INVALID_INPUT_VALUE

    e.nom = name

    if city != e.ville:
      gps_coords = get_location_of_company(city)
      e.ville = city
      e.lat = gps_coords[0]
      e.lng = gps_coords[1]


    if type(size) is not str:
      return ERRORS.INVALID_INPUT_TYPE

    valid_comp_size = {"small", "big", "medium", "very_big"}
    if size not in valid_comp_size:
      return ERRORS.UNEXPECTED_INPUT_VALUE
    e.taille = size

    if type(status) is not str:
      return ERRORS.INVALID_INPUT_TYPE

    valid_comp_status = {"public", "private"}
    if status not in valid_comp_status:
      return ERRORS.UNEXPECTED_INPUT_VALUE
    e.statut = status

    db_session.commit()

    return flask.jsonify(e)


  @app.route('/company/all')
  @login_required
  def fetch_company():
    return flask.jsonify(Entreprise.query.all())

  
  @app.route('/company/<int:id>', methods=["GET"])
  @login_required
  def get_company(id: int):
    e = Entreprise.query.filter_by(id_entreprise=id).one_or_none()

    if not e:
      return ERRORS.COMPANY_NOT_FOUND

    return flask.jsonify(e)


  @app.route('/company/merge', methods=["POST"])
  @login_required
  def merge_companies():
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

    main_company: Entreprise = Entreprise.query.filter_by(id_entreprise=main).one_or_none()

    if not main_company:
      return ERRORS.COMPANY_NOT_FOUND

    children_companies: List[Entreprise] = []
    for c in children:
      if type(c) is not int:
        return ERRORS.BAD_REQUEST

      ent = Entreprise.query.filter_by(id_entreprise=c).one_or_none()
      if not ent:
        return ERRORS.COMPANY_NOT_FOUND

      children_companies.append(ent)

    # For each job/internship relied to children_companies, set main_company
    for c in children_companies:
      Emploi.query.filter_by(id_entreprise=c.id_entreprise).update({'id_entreprise': main_company.id_entreprise})
      Stage.query.filter_by(id_entreprise=c.id_entreprise).update({'id_entreprise': main_company.id_entreprise})

    # Delete every children company
    for c in children_companies:
      Contact.query.filter_by(id_entreprise=c.id_entreprise).update({'id_entreprise': main_company.id_entreprise})
      db_session.delete(c)

    db_session.commit()
    return ""


  @app.route('/company/<int:id>', methods=["DELETE"])
  @login_required
  def delete_company(id: int):
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    c: Entreprise = Entreprise.query.filter_by(id_entreprise=id).one_or_none()

    if not c:
      return ""

    # Delete all manuel
    Stage.query.filter_by(id_entreprise=id).delete()
    Emploi.query.filter_by(id_entreprise=id).delete()
    Contact.query.filter_by(id_entreprise=id).delete()
    
    db_session.delete(c)
    db_session.commit()

    return ""


  @app.route('/company/map')
  def map_of_company():
    with engine.connect() as conn:
      rs = conn.execute("""
        SELECT DISTINCT ville, lat, lng, COUNT(*) as count 
        FROM Entreprise e 
        WHERE lat IS NOT NULL 
        GROUP BY ville, lat, lng
      """)

      villes = []
      for row in rs:
        villes.append(row)

      return flask.jsonify([{"lat": x[1], "lng": x[2], "town": x[0], "count": int(x[3])} for x in villes])

    return ERRORS.SERVER_ERROR
