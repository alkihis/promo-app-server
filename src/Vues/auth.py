import flask
from helpers import get_request, is_teacher, get_user
from Models.Token import Token
import uuid
from server import db_session
from errors import ERRORS
from flask_login import login_required

def define_auth_routes(app: flask.Flask):
  ## For teacher
  @app.route('/auth/login', methods=['POST'])
  def login_for_teacher():
    r = get_request()

    # TODO make verif for password
    if r.is_json and 'password' in r.json and r.json['password'] == "DEFINED_PASSWORD":
      # Cherche si un token existe
      t: Token = Token.query.filter_by(type=True).one_or_none()

      if not t:
        ## Create token
        new_token = str(uuid.uuid4())

        # Register token
        t = Token.create(token=new_token, type=True)
        db_session.add(t)
        db_session.commit()

      return flask.jsonify({'token': t.token})
    else:
      return ERRORS.error("INVALID_PASSWORD")

  @app.route('/auth/validate', methods=['POST'])
  def login_for_student():
    r = get_request()

    if r.is_json and 'token' in r.json:
      token = r.json['token']

      # Check for token
      t: Token = Token.query.filter_by(token=token).one_or_none()

      if not t:
        return ERRORS.error("INVALID_TOKEN")
      
      # Empty HTTP 200
      return ""

    else:
      return ERRORS.error("BAD_REQUEST")


  @app.route('/auth/redirect')
  def redirect_to_logged():
    r = get_request()

    if r.args.get('token'):
      return flask.redirect('/', code=302)
    else:
      return "", 401

  @app.route('/auth/<token>', methods=["DELETE"])
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

  ## TODO REMOVE
  @app.route('/token/all')
  def see_token():
    return flask.jsonify(Token.query.all())
