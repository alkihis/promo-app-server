from flask import Flask, jsonify, Response
from helpers import getDb
from server import Etudiant, db_session
from datetime import date

### Define a classic route, and receive Flask app
def get_student_routes(app: Flask):
  ## define a placeholder endpoint, TODO to replace
  @app.route('/student/<int:identifier>', methods=['GET'])
  def getStudent(identifier: int) -> Response:
    e: Etudiant = Etudiant.query.filter_by(id_etu=identifier).one_or_none()

    return jsonify(e)

  @app.route('/student/create/<nom>/<prenom>', methods=['GET', 'PUT'])
  def putStudent(nom: str, prenom: str) -> Response:
    etu = Etudiant.create(nom, prenom, "hello@pouet.fr", date.today(), "1902/1903")

    db_session.add(etu)
    db_session.commit()

    return jsonify(etu)
    
  @app.route('/student/all')
  def allStudents():
    return jsonify(Etudiant.query.all())