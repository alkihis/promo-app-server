from flask import Flask, jsonify, Response
from server import db_session
from Models.Etudiant import Etudiant
from Models.Token import Token
from datetime import date
import uuid

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

    ## Crée un token pour l'étudiant
    new_token = str(uuid.uuid4())
    t = Token.create(token=new_token, type=False, id_etu=etu.id_etu)
    db_session.add(t)
    db_session.commit()

    return jsonify(etu)
    
  @app.route('/student/all')
  def allStudents():
    return jsonify(Etudiant.query.all())
    