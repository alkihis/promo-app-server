import flask
from helpers import get_request, is_teacher, get_user, get_teacher_password_hash, get_or_create_token_for
from Models.Token import Token
from Models.Etudiant import Etudiant
import uuid
from server import db_session, bcrypt
from errors import ERRORS
from flask_login import login_required
from models_helpers import send_welcome_mail

def define_auth_routes(app: flask.Flask):
  @app.route('/token/recover')
  def recover_token():
    r = get_request()

    if not 'email' in r.args:
      return ERRORS.BAD_REQUEST

    # test si un étudiant avec cet email existe
    e: Etudiant = Etudiant.query.filter_by(mail=r.args['email']).one_or_none()

    if not e:
      # Etu introuvable
      return ERRORS.STUDENT_NOT_FOUND

    send_welcome_mail(e.id_etu)

    return ""


  ## For teacher
  @app.route('/auth/login', methods=['POST'])
  def login_for_teacher():
    r = get_request()

    # TODO make verif for password
    if r.is_json and 'password' in r.json and bcrypt.check_password_hash(get_teacher_password_hash(), r.json['password']):
      # Cherche si un token existe
      t: Token = get_or_create_token_for(None, True)

      return flask.jsonify({'token': t.token})
    else:
      return ERRORS.INVALID_PASSWORD

  ## Validate (check validity) a token
  @app.route('/auth/validate', methods=['POST'])
  def login_for_student():
    r = get_request()

    if r.is_json and 'token' in r.json:
      token = r.json['token']

      # Check for token
      t: Token = Token.query.filter_by(token=token).one_or_none()

      if not t:
        return ERRORS.INVALID_TOKEN

      # Empty HTTP 200
      return flask.jsonify({"is_teacher": t.teacher})

    else:
      return ERRORS.BAD_REQUEST

  ## Invalidate a token (remove the possibility of login)
  @app.route('/auth/token', methods=["DELETE"])
  @login_required
  def invalidate_token():
    r = get_request()
    token = r.headers.get('Authorization').replace('Bearer ', '', 1)

    if is_teacher():
      Token.query.filter_by(token=token).delete()
      db_session.commit()
      return ""
    else:
      current_etu_id = get_user().id_etu
      t: Token = Token.query.filter_by(token=token).one_or_none()

      if not t:
        return ERRORS.NOT_FOUND

      if t.id_etu == current_etu_id:
        db_session.delete(t)
        db_session.commit()
      else:
        return ERRORS.INVALID_CREDENTIALS

  ## Get all tokens linked to logged user
  @app.route('/token/all')
  @login_required
  def see_token():
    page = 0
    length = 20
    r = get_request()

    if r.args.get('page') is not None:
      try:
        choosen_page = int(r.args.get('page'))

        if choosen_page >= 0:
          page = choosen_page
      except:
        return ERRORS.BAD_REQUEST

    if r.args.get('count') is not None:
      try:
        choosen_count = int(r.args.get('count'))

        if 0 < choosen_count <= 100:
          length = choosen_count
      except:
        return ERRORS.BAD_REQUEST

    start = page * length
    end = (page + 1) * length

    # Teachers are allowed to see tokens of all users (may be heavy)
    if is_teacher():
      return flask.jsonify(Token.query.all()[start:end])

    # Send all tokens of logged user
    id_etu = get_user().id_etu
    return flask.jsonify(Token.query.filter_by(id_etu=id_etu).all()[start:end])
