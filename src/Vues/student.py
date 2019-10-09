import flask
from Models.Etudiant import Etudiant
### Vues pour l'API /student

def student_routes(app: flask.Flask):
  # Get a single Etudiant by ID
  @app.route('/student/<int:id>')
  def get_id(id: int):
    e: Etudiant = Etudiant.query.filter_by(id_etu=identifier).one_or_none()
    return flask.jsonify(e)


