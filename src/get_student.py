from flask import Flask, jsonify, Response
from helpers import getDb

### Define a classic route, and receive Flask app
def get_student_routes(app: Flask):
  ## define a placeholder endpoint, TODO to replace
  @app.route('/student/<int:identifier>', methods=['GET'])
  def getStudent(identifier: int) -> Response:
    return jsonify({ 'id': identifier })
    