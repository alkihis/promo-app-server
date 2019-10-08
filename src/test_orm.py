from server import db_session, Etudiant
import datetime


def test():
  admin = Etudiant.create("admin", "", "etudiant@admin.fr", datetime.date.today(), "2017/2018", "2017/2018")

  db_session.add(admin)
  db_session.commit()

