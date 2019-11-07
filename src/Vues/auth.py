import flask
from helpers import get_request, is_teacher, get_user
from Models.Token import Token
import uuid
from server import db_session
from errors import ERRORS
from flask_login import login_required

PASSWORD_FOR_TEACHER = "DEFINED_PASSWORD"

def define_auth_routes(app: flask.Flask):
  ## For teacher
  @app.route('/auth/login', methods=['POST'])
  def login_for_teacher():
    r = get_request()

    # TODO make verif for password
    if r.is_json and 'password' in r.json and r.json['password'] == PASSWORD_FOR_TEACHER:
      # Cherche si un token existe
      t: Token = Token.query.filter_by(teacher=True).one_or_none()

      if not t:
        ## Create token
        new_token = str(uuid.uuid4())

        # Register token
        t = Token.create(token=new_token, teacher=True)
        db_session.add(t)
        db_session.commit()

      return flask.jsonify({'token': t.token})
    else:
      return ERRORS.error("INVALID_PASSWORD")

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

  # Redirect to home (useless)
  @app.route('/auth/redirect')
  def redirect_to_logged():
    r = get_request()

    if r.args.get('token'):
      return flask.redirect('/', code=302)
    else:
      return "", 401

  ## Invalidate a token (remove the possibility of login)
  @app.route('/auth/token', methods=["DELETE"])
  @login_required
  def invalidate_token():
    if is_teacher():
      Token.query.filter_by(token=token).delete()
      db_session.commit()
      return ""
    else:
      current_etu_id = get_user().id_etu
      t: Token = Token.query.filter_by(token=token).one_or_none()

      if not t:
        return ERRORS.error("NOT_FOUND")

      if t.id_etu == current_etu_id:
        db_session.delete(t)
        db_session.commit()
      else:
        return ERRORS.error("INVALID_CREDENTIALS")

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

        if choosen_count > 0 and choosen_count <= 100:
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
