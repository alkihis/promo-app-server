from flask import Flask, jsonify, Response
from helpers import getDb
from server import Etudiant, db_session

### Define a classic route, and receive Flask app
def get_student_routes(app: Flask):
  ## define a placeholder endpoint, TODO to replace
  @app.route('/student/<int:identifier>', methods=['GET'])
  def getStudent(identifier: int) -> Response:
    e: Etudiant = Etudiant.query.filter_by(id_etu=identifier).one_or_none()

    return jsonify(e)
    