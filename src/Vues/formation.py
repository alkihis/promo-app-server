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
from models_helpers import get_student_or_none

def define_formation_endpoints(app: flask.Flask):
  @app.route('/formation/create', methods=["POST"])
  @login_required
  def create_formation():
    r = get_request()
    stu: Etudiant = get_student_or_none()

    if not stu or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'name', 'location', 'level'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    branch, location, level = data['name'], data['location'], data['level']


    if type(branch) is not str:
      return ERRORS.BAD_REQUEST

    # Check level: must be in ENUM
    if type(level) is not str:
      return ERRORS.BAD_REQUEST
    
    valid_levels = {"licence", "master", "phd", "other"}
    if level not in valid_levels:
      return ERRORS.BAD_REQUEST


    ## Search for similar formations TODO improve search
    f = Formation.query.filter(
      and_(
        Formation.filiere.ilike(f"{branch}"), 
        Formation.lieu.ilike(f"{location}"), 
        Formation.niveau.ilike(f"{level}")
      )
    ).all()

    if len(f):
      return flask.jsonify(f[0])

    # Create new formation
    form = Formation.create(filiere=branch, lieu=location, niveau=level)
    db_session.add(form)
    db_session.commit()

    return flask.jsonify(form), 201


  @app.route('/formation/modify', methods=["POST"])
  @login_required
  def modify_formation():
    r = get_request()
    stu: Etudiant = get_student_or_none()

    if not stu or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not {'branch', 'location', 'level', 'id'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    branch, location, level, id_formation = data['branch'], data['location'], data['level'], data['id']

    if type(id_formation) is not int:
      return ERRORS.BAD_REQUEST

    # TODO check level: must be in ENUM
    f: Formation = Formation.query.filter_by(id_form=id_formation).one_or_none()

    if not f:
      return ERRORS.RESOURCE_NOT_FOUND

    # TODO check each setting validity
    if type(branch) is not str:
      return ERRORS.BAD_REQUEST
    f.filiere = branch
    
    # Query le lieu pr obtenir lat & long si lieu != location
    if f.lieu != location:
      f.lieu = location

    if type(level) is not str:
      return ERRORS.BAD_REQUEST

    valid_levels = {"licence", "master", "phd", "other"}
    if level not in valid_levels:
      return ERRORS.BAD_REQUEST
    f.niveau = level
    db_session.commit()

    return flask.jsonify(f)


  @app.route('/formation/all')
  @login_required
  def fetch_locations():
    return flask.jsonify(Formation.query.all())


  @app.route('/formation/merge', methods=["POST"])
  @login_required
  def merge_formations():
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

    main_formation: Formation = Formation.query.filter_by(id_form=main).one_or_none()

    if not main_formation:
      return ERRORS.RESOURCE_NOT_FOUND

    children_formations: List[Formation] = []
    for c in children:
      if type(c) is not int:
        return ERRORS.BAD_REQUEST

      ent = Formation.query.filter_by(id_form=c).one_or_none()
      if not ent:
        return ERRORS.RESOURCE_NOT_FOUND

      children_formations.append(ent)

    # For each student relied to children_formations, set main_formation
    for c in children_formations:
      Etudiant.query.filter_by(reorientation=c.id_form).update({'reorientation': main_formation.id_form})
      Etudiant.query.filter_by(cursus_anterieur=c.id_form).update({'cursus_anterieur': main_formation.id_form})

    # Delete every children company
    for c in children_formations:
      db_session.delete(c)

    db_session.commit()
    return ""

  @app.route('/formation/<int:id>', methods=["DELETE"])
  @login_required
  def delete_formation(id: int):
    # Get logged etudiant
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    form: Formation = Formation.query.filter_by(id_form=id).one_or_none()

    if not form:
      return ""

    # Supprime les formations des étudiants
    for etu in Etudiant.query.filter_by(cursus_anterieur=id).all():
      etu.cursus_anterieur = None

    for etu in Etudiant.query.filter_by(reorientation=id).all():
      e.reorientation = None
  
    db_session.commit()

    return ""
