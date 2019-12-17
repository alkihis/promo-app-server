import flask
from Models.Entreprise import Entreprise
from Models.Domaine import Domaine
from Models.Contact import Contact
from Models.Etudiant import Etudiant
from Models.Emploi import Emploi
from flask_login import login_required
from helpers import is_teacher, get_request, get_user, is_truthy, convert_date
from models_helpers import get_student_or_none
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict


def define_job_endpoints(app: flask.Flask):
  @app.route('/job/create', methods=["POST"])
  @login_required
  def make_emploi():
    r = get_request()
    stu = get_student_or_none()

    if not stu or not r.is_json:
      print("Student is invalid")
      return ERRORS.BAD_REQUEST

    user_id = stu.id_etu
    data = r.json

    ########### TODO: check parametres emplois

    if not {'start', 'end', 'contract', 'salary', 'level', 'company', 'domain', 'contact'} <= set(data):
      print("Parameters")
      print(list(set(data)))
      return ERRORS.MISSING_PARAMETERS

    start, end, contract, salary, level, id_entreprise = data['start'], data['end'], data['contract'], data['salary'], data['level'], data['company']
    domain, id_contact = data['domain'], data['contact']

    list_d: List[Domaine] = Domaine.query.filter_by(domaine=domain).all()

    if not len(list_d):
      print("Domain is not correct")
      return ERRORS.BAD_REQUEST
    try:
      id_entreprise = int(id_entreprise)

      if salary is not None:
        salary = int(salary)

      if id_contact is not None:
        id_contact = int(id_contact)
    except:
      print("ID value error")
      return ERRORS.BAD_REQUEST

    id_domain = list_d[0].id_domaine

    try:
      start = convert_date(start)
    except:
      print("Start date error")
      return ERRORS.BAD_REQUEST

    if end is not None:
      try:
        end = convert_date(end)
      except:
        print("End date error")
        return ERRORS.BAD_REQUEST

    # Teste si l'entreprise existe
    e = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()
    if not e:
      print("Company not found")
      return ERRORS.BAD_REQUEST

    # Teste si le contact existe
    if id_contact is not None:
      c = Contact.query.filter_by(id_contact=id_contact).one_or_none()
      if not c:
        print("Contact not found")
        return ERRORS.BAD_REQUEST


    #CHECK Contract in ENUM
    if type(contract) is not str:
      return ERRORS.INVALID_INPUT_TYPE
    
    #as_describe in client part interfaces.ts jobtypes
    valid_contracts = {"cdi", "alternance", "cdd", "these"}
    if contract not in valid_contracts:
        return ERRORS.UNEXPECTED_INPUT_VALUE


    #CHECK Level in ENUM
    if type(level) is not str:
      return ERRORS.INVALID_INPUT_TYPE
    
    #as_describe in client part interfaces.ts joblevels
    valid_levels = {"technicien", "ingenieur", "doctorant", "alternant"}
    if level not in valid_levels:
      return ERRORS.UNEXPECTED_INPUT_VALUE
    # Create new emploi
    stu.refresh_update()
    emp = Emploi.create(
      debut=start, 
      fin=end, 
      contrat=contract, 
      niveau=level,
      id_entreprise=id_entreprise, 
      id_domaine=id_domain, 
      id_contact=id_contact, 
      id_etu=user_id, 
      salaire=salary
    )
    db_session.add(emp)
    db_session.commit()

    return flask.jsonify(emp), 201

  @app.route('/job/modify', methods=['POST'])
  @login_required
  def modify_job():
    r = get_request()
    stu = get_student_or_none()

    if not r.is_json:
      print("Student is invalid")
      return ERRORS.BAD_REQUEST

    data = r.json

    ########### TODO: check parametres emplois

    if not {'job'} <= set(data):
      return ERRORS.MISSING_PARAMETERS

    job_id = data['job']

    try:
      job_id = int(data['job'])
    except:
      return ERRORS.BAD_REQUEST

    job: Emploi = Emploi.query.filter_by(id_emploi=job_id).one_or_none()

    if not job:
      return ERRORS.RESOURCE_NOT_FOUND

    if not is_teacher() and job.id_etu != stu.id_etu:
      return ERRORS.INVALID_CREDENTIALS

    # Modification !
    if 'domain' in data:
      domain = data['domain']
      list_d: List[Domaine] = Domaine.query.filter_by(domaine=domain).all()

      if not len(list_d):
        print("Domain is not correct")
        return ERRORS.BAD_REQUEST

      job.id_domaine = list_d[0].id_domaine

    if 'company' in data:
      try:
        id_entreprise = int(data['company'])
      except:
        db_session.rollback()
        return ERRORS.BAD_REQUEST

      # Teste si l'entreprise existe
      e: Entreprise = Entreprise.query.filter_by(id_entreprise=id_entreprise).one_or_none()
      if not e:
        print("Company not found")
        db_session.rollback()
        return ERRORS.BAD_REQUEST

      job.id_entreprise = e.id_entreprise

    if 'start' in data:
      start = data['start']

      try:
        start = convert_date(start)
      except:
        print("Start date error")
        db_session.rollback()
        return ERRORS.INVALID_DATE

      job.debut = start
  
    if 'end' in data:
      if data['end'] is None:
        job.fin = None
      else:
        try:
          end = convert_date(data['end'])
        except:
          print("End date error")
          db_session.rollback()
          return ERRORS.INVALID_DATE

        job.fin = end

    if 'level' in data:
      level = data['level']
      #CHECK Level in ENUM
      if type(level) is not str:
        db_session.rollback()
        return ERRORS.INVALID_INPUT_TYPE
      
      #as_describe in client part interfaces.ts joblevels
      valid_levels = {"technicien", "ingenieur", "doctorant", "alternant"}
      if level not in valid_levels:
        db_session.rollback()
        return ERRORS.UNEXPECTED_INPUT_VALUE
      
      job.niveau = data['level']
    
    if 'contract' in data:
      contract = data['contract']
      #Check contract in ENUM
      if type(contract) is not str:
        db_session.rollback()
        return ERRORS.INVALID_INPUT_TYPE
    
      #as_describe in client part interfaces.ts jobtypes
      valid_contracts = {"cdi", "alternance", "cdd", "these"}
      if contract not in valid_contracts:
        db_session.rollback()
        return ERRORS.UNEXPECTED_INPUT_VALUE

      job.contrat = contract

    if 'salary' in data:
      if data['salary'] is None:
        job.salaire = None
      else:
        try:
          salaire = int(data['salary'])
          job.salaire = salaire
        except:
          db_session.rollback()
          return ERRORS.INVALID_INPUT_TYPE


    if 'contact' in data:
      if data['contact'] is None:
        job.id_contact = None
      else:
        try:
          id_contact = int(data['contact'])

          c = Contact.query.filter_by(id_contact=id_contact).one_or_none()
          if not c:
            print("Contact not found")
            db_session.rollback()
            return ERRORS.BAD_REQUEST
        except:
          db_session.rollback()
          return ERRORS.BAD_REQUEST

    stu.refresh_update()
    db_session.commit()

    return flask.jsonify(job)

  @app.route('/job/all')
  @login_required
  def fetch_jobs_for_student():
    r = get_request()

    stu: Etudiant = get_student_or_none()
    if not stu:
      return ERRORS.BAD_REQUEST

    return flask.jsonify(Emploi.query.filter_by(id_etu=stu.id_etu).all())


  @app.route('/job/actives')
  @login_required
  def get_last_actives_job():
    stu = get_student_or_none()

    if not stu:
      return ERRORS.BAD_REQUEST

    jobs = Emploi.query.filter_by(id_etu=stu.id_etu, fin=None).order_by(Emploi.debut.desc()).all()

    if not jobs:
      return flask.jsonify([])

    return flask.jsonify(jobs)


  @app.route('/job/<int:id>', methods=["GET"])
  @login_required
  def get_a_job(id: int):
    job: Emploi = Emploi.query.filter_by(id_emploi=id).one_or_none()

    if job is None:
      return ERRORS.RESOURCE_NOT_FOUND

    stu = get_student_or_none()

    if not stu:
      return ERRORS.BAD_REQUEST

    if not is_teacher() and stu.id_etu != job.id_etu:
      return ERRORS.INVALID_CREDENTIALS

    return flask.jsonify(job)


  @app.route('/job/<int:id>', methods=["DELETE"])
  @login_required
  def delete_job(id: int):
    job: Emploi = Emploi.query.filter_by(id_emploi=id).one_or_none()

    if job is None:
      return "" # 200 OK deleted

    stu = get_student_or_none()

    if not stu:
      return ERRORS.BAD_REQUEST

    if not is_teacher() and stu.id_etu != job.id_etu:
      return ERRORS.INVALID_CREDENTIALS

    # TODO properly delete job (maybe cascade is not working)
    stu.refresh_update()
    db_session.delete(job)
    db_session.commit()

    return ""


