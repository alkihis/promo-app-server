import flask
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant
from Models.Stage import Stage
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy
from models_helpers import get_student_or_none
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict


def define_internship_endpoints(app: flask.Flask):
  @app.route('/internship/create', methods=["POST"])
  @login_required
  def make_internship():
    r = get_request()
    stu = get_student_or_none()

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    if not stu:
      return ERRORS.STUDENT_NOT_FOUND

    data = r.json

    if not {'promo_year', 'company', 'domain', 'contact'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    promo_year, id_entreprise, domain, id_contact = data['promo_year'], data['company'], data['domain'], data['contact']
    
    # Check if promo_year is okay for this student !
    if not int(stu.annee_entree) <= int(data['promo_year']) <= int(stu.annee_sortie):
      return ERRORS.INVALID_DATE

    ## Check company id
    ent: Entreprise = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()

    if not ent:
      return ERRORS.COMPANY_NOT_FOUND

    ##  Domain to id
    dom: Domaine = Domaine.query.filter_by(domaine=domain).one_or_none()

    if not dom:
      return ERRORS.DOMAIN_NOT_FOUND
    
    id_domain = dom.id_domaine


    ## Check contact id
    if id_contact is not None:
      cont: Contact = Contact.query.filter_by(id_contact=id_contact).one_or_none()

      if not cont:
        return ERRORS.CONTACT_NOT_FOUND

    # Create new internship
    stu.refresh_update()
    inter = Stage.create(
      promo=promo_year, 
      id_entreprise=int(id_entreprise), 
      id_domaine=id_domain, 
      id_contact=int(id_contact) if id_contact is not None else None, 
      id_etu=stu.id_etu
    )
    db_session.add(inter)
    db_session.commit()

    return flask.jsonify(inter), 201


  @app.route('/internship/modify', methods=["POST"])
  @login_required
  def modify_internship():
    r = get_request()
    stu = get_student_or_none()

    if not stu or not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if not 'internship' in data:
      return ERRORS.MISSING_PARAMETERS

    internship: Stage = Stage.query.filter_by(id_stage=data['internship']).one_or_none()

    if not internship:
      return ERRORS.RESOURCE_NOT_FOUND

    if not is_teacher() and internship.id_etu != stu.id_etu:
      return ERRORS.INVALID_CREDENTIALS

    if 'promo_year' in data:
      internship.promo = data['promo_year']

    if 'company' in data:
      ent: Entreprise = Entreprise.query.filter_by(id_entreprise=data['company']).one_or_none()

      if not ent:
        db_session.rollback()
        return ERRORS.COMPANY_NOT_FOUND

      internship.id_entreprise = ent.id_entreprise

    if 'domain' in data:
      dom: Domaine = Domaine.query.filter_by(domaine=data['domain']).one_or_none()

      if not dom:
        db_session.rollback()
        return ERRORS.DOMAIN_NOT_FOUND

      internship.id_domaine = dom.id_domaine

    if 'contact' in data:
      if data['contact'] is None:
        internship.id_contact = None
      else:
        cont: Contact = Contact.query.filter_by(id_contact=data['contact']).one_or_none()

        if not cont:
          db_session.rollback()
          return ERRORS.CONTACT_NOT_FOUND

        internship.id_contact = cont.id_contact

    stu.refresh_update()
    db_session.commit()

    return flask.jsonify(internship)


  @app.route('/internship/all')
  @login_required
  def fetch_intership():
    stu: Etudiant = get_student_or_none()
    if not stu:
      return ERRORS.STUDENT_NOT_FOUND

    return flask.jsonify(Stage.query.filter_by(id_etu=stu.id_etu).all())


  @app.route('/internship/<int:id>', methods=["GET"])
  @login_required
  def get_a_internship(id: int):
    internship: Stage = Stage.query.filter_by(id_stage=id).one_or_none()

    if internship is None:
      return ERRORS.RESOURCE_NOT_FOUND

    stu = get_student_or_none()

    if not is_teacher():
      if not stu or stu.id_etu != internship.id_etu:
        return ERRORS.INVALID_CREDENTIALS

    return flask.jsonify(internship)


  @app.route('/internship/<int:id>', methods=["DELETE"])
  @login_required
  def delete_internship(id: int):
    internship: Stage = Stage.query.filter_by(id_stage=id).one_or_none()

    if internship is None:
      return "" # 200 OK deleted

    stu = get_student_or_none()

    if not stu:
      return ERRORS.STUDENT_NOT_FOUND

    if not is_teacher() and stu.id_etu != internship.id_etu:
      return ERRORS.INVALID_CREDENTIALS

    # Properly delete internship (maybe cascade is not working)
    stu.refresh_update()
    db_session.delete(internship)
    db_session.commit()

    return ""

