from flask_login import LoginManager, login_user, user_loaded_from_header
import Models.Etudiant
import Models.Token
from typing import Union
from flask import g, Request
from flask.sessions import SecureCookieSessionInterface
from flask_login import user_loaded_from_header

class User:
  def __init__(self, id_etu = 0, teacher = False):
    self.id_etu = id_etu
    self.teacher = teacher
    self.is_authenticated = True
    self.is_active = True
    self.is_anonymous = False

  def get_id(self) -> str:
    return str(self.id_etu)

  def get_etu(self) -> Union[Models.Etudiant.Etudiant, None]:
    if self.id_etu == 0:
      return None
    else:
      return Models.Etudiant.Etudiant.query.filter_by(id_etu=int(id)).one_or_none()

  @staticmethod
  def get(id: str, teacher = False):
    if id == "0" and teacher:
      return User(teacher=True)
    else:
      ## Test existance of user_id
      etu = Models.Etudiant.Etudiant.query.filter_by(id_etu=int(id)).one_or_none()

      if etu:
        return User(int(id))
      else:
        return None

  def __repr__(self):
    return f"""
      {self.id_etu} / {self.teacher}
    """

login_manager = LoginManager()

def set_app_login_manager(app):
  login_manager.setup_app(app)
  app.session_interface = CustomSessionInterface()

class CustomSessionInterface(SecureCookieSessionInterface):
  """Prevent creating session from API requests."""
  def save_session(self, *args, **kwargs):
    if g.get('login_via_header'):
      return
    return super(CustomSessionInterface, self).save_session(*args, **kwargs)

@user_loaded_from_header.connect
def user_loaded_from_header(self, user=None):
  g.login_via_header = True

@login_manager.request_loader
def load_user_from_request(request: Request):
  # Try to login using Basic Auth
  api_key = request.headers.get('Authorization')
  if api_key:
    api_key = api_key.replace('Bearer ', '', 1)

    token = Models.Token.Token.query.filter_by(token=api_key).one_or_none()

    if token:
      if token.id_etu:
        return User.get(str(token.id_etu))
      elif token.teacher:
        return User.get('0', teacher=True)

  # finally, return None if both methods did not login the user
  return None
  