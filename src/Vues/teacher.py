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

def define_teacher_endpoints(app: flask.Blueprint):
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
