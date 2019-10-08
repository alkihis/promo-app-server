from server import db_session
from Models.Etudiant import Etudiant
import datetime


def test():
  admin = Etudiant.create("admin", "", "etudiant@admin.fr", datetime.date.today(), "2017/2018", "2017/2018")

  db_session.add(admin)
  db_session.commit()

