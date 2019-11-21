from Models.Etudiant import Etudiant
from helpers import get_user, is_teacher, get_request
from typing import Optional, List

def get_etu_object_for_logged_user() -> Optional[Etudiant]:
  user = get_user()

  if user and user.id_etu:
    return Etudiant.query.filter_by(id_etu=user.id_etu).one_or_none()

def get_student_or_none() -> Optional[Etudiant]:
  r = get_request()

  if is_teacher():
    if r.args.get('id') or r.args.get('user_id'):
      try:
        u_id = r.args.get('id') if r.args.get('id') else r.args.get('user_id')
        return Etudiant.query.filter_by(id_etu=int(u_id)).one_or_none()
      except:
        return None
    elif r.is_json and 'id' in r.json or 'user_id' in r.json:
      try:
        u_id = r.json['id'] if 'id' in r.json else r.json['user_id']
        return Etudiant.query.filter_by(id_etu=int(u_id)).one_or_none()
      except:
        return None
  else:
    return get_etu_object_for_logged_user()


def send_basic_mail(content: str, to: List[str], obj: str):
  # TODO interpolation de \student (par exemple)

  for student in to:
    # todo send the mail
    pass

