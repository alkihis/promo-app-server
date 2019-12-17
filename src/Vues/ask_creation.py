import flask
from helpers import get_request, is_teacher, generate_random_token
from models_helpers import create_a_student, send_invite_create_profile_mail
from Models.AskCreation import AskCreation
from Models.Etudiant import Etudiant
import uuid
from server import db_session
from errors import ERRORS
from flask_login import login_required

def define_ask_creation_routes(app: flask.Blueprint):
  @app.route('/ask_creation/create', methods=["POST"])
  @login_required
  def create_token_ask():
    if not is_teacher():
      return ERRORS.INVALID_CREDENTIALS

    r = get_request()

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if 'mail' not in data:
      return ERRORS.BAD_REQUEST

    e = Etudiant.query.filter_by(mail=data['mail']).one_or_none()

    if e:
      return ERRORS.CONFLICT

    mail = data['mail']

    # Send the mail
    send_invite_create_profile_mail(mail)

    return ""


  @app.route('/ask_creation/new', methods=['POST'])
  def create_a_student_from_token():
    r = get_request()

    if not r.is_json:
      return ERRORS.BAD_REQUEST

    data = r.json

    if 'token' not in data:
      return ERRORS.BAD_REQUEST

    token = data['token']
    a: AskCreation = AskCreation.query.filter_by(token=token).one_or_none()

    if not a:
      # Token does not exists TODO message CLIENT
      return ERRORS.RESOURCE_NOT_FOUND

    etu = create_a_student(data)

    if type(etu) is not Etudiant:
      return etu  # this is an error

    AskCreation.query.filter_by(token=token).delete()
    db_session.commit()

    return flask.jsonify(etu)
