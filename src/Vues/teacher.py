import flask
from Models.Emploi import Emploi
from Models.Etudiant import Etudiant
from Models.Stage import Stage
from flask_login import login_required
from models_helpers import get_student_or_none
from helpers import is_teacher, get_request, is_truthy
from errors import ERRORS
from server import db_session
from typing import List, Tuple, Dict

def define_teacher_endpoints(app: flask.Blueprint):
  @app.route('/teacher/home_stats')
  @login_required
  def home_statistics():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS


    return flask.jsonify({})
