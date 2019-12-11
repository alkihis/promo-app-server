import flask
from Models.Emploi import Emploi
from Models.Etudiant import Etudiant
from Models.Entreprise import Entreprise
from Models.Stage import Stage
from flask_login import login_required
from models_helpers import get_student_or_none
from helpers import is_teacher, get_request, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict
from sqlalchemy import func
from datetime import date

def define_teacher_endpoints(app: flask.Blueprint):
  @app.route('/teacher/stats')
  # @login_required
  def main_stats():
    # if not is_teacher():
      # return ERRORS.INVALID_CREDENTIALS

    # Statistiques de base 
    # (deux graphiques: 
    # Les deux concernes les étudiants diplômés et sortis du master
    # le taux d'emploi après 1 an
    # et la répartition des emplois public / privé
    # )

    students: List[Etudiant] = Etudiant.query.filter(Etudiant.diplome == True, Etudiant.annee_sortie != None).all()

    # { 'year': { 'count': number, 'inserted': number } }
    annee_taux_d_insertion = {}

    # { 'year': { 'private': number, 'public': number } }
    repartition_public_prive = {}

    # now_year = date.today().year

    for student in students:
      emplois: List[Emploi] = Emploi.query.filter(Emploi.id_etu == student.id_etu).all()

      # Trouver emplois
      current_year = int(student.annee_sortie)


      inserted = False

      for emploi in emplois:
        start = int(emploi.debut.year)
        end = None if not emploi.fin else int(emploi.fin.year)
        if end:
          if start <= current_year and end > current_year:
            # Ok !
            inserted = True
        else:
          inserted = True
        
        private = emploi.entreprise.statut != "public"

        if current_year in repartition_public_prive:
          repartition_public_prive[current_year]["private" if private else "public"] += 1
        else:
          repartition_public_prive[current_year] = {
            "private": 1 if private else 0,
            "public": 1 if not private else 0,
          }

      if current_year not in annee_taux_d_insertion:
        annee_taux_d_insertion[current_year] = {
          "count": 0,
          "inserted": 0
        }

      if inserted:
        annee_taux_d_insertion[current_year]['inserted'] += 1

      annee_taux_d_insertion[current_year]['count'] += 1

    return flask.jsonify(insertion_stats=annee_taux_d_insertion, public_private=repartition_public_prive)

  @app.route('/teacher/home_stats')
  @login_required
  def home_statistics():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS


    # Obtient le nombre d'étudiants enregistrés
    stu_count = Etudiant.query.count()

    # Nombre d'étudiant occupant un emploi actuellement
    stu_with_job_count = Etudiant.query.join(Emploi).filter_by(fin=None).distinct(Etudiant.id_etu).count()

    # Nombre d'entreprises dans lesquelles les étudiants occupent actuellement un emploi
    entreprises_count = Entreprise.query.join(Emploi).filter_by(fin=None).distinct(Entreprise.id_entreprise).count()

    # Nombre d'étudiants diplômés
    stu_graduated_count = Etudiant.query.filter_by(diplome=True).count()

    # Nombre d'étudiants en formation
    stu_in_formation_count = Etudiant.query.filter_by(diplome=False, annee_sortie=None).count()

    # Nombre d'étudiants en thèse / ayant fait une thèse
    stu_in_thesis_count = Etudiant.query.join(Emploi).filter_by(contrat="these").count()

    return flask.jsonify({
      "students": stu_count,
      "students_currently_working": stu_with_job_count,
      "companies_with_work": entreprises_count,
      "graduated": stu_graduated_count,
      "thesis": stu_in_thesis_count,
      "in_formation": stu_in_formation_count,
    })
