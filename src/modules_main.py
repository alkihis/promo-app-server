from flask import jsonify, request
from flask_cors import CORS
from server import app, db_session

if __name__ == "__main__":
  print("Please run app.py instead. This should not be the main file.")
  exit()

## Module initializer
#### Init modules
# Make app CORS-ready
CORS(app)

# Init the login manager
from login_handler import set_app_login_manager
set_app_login_manager(app)

## Import the module and the apply function, and give app
from Vues.get_student import get_student_routes
# get_student_routes(app)

from errors import classic_errors
classic_errors(app)

from Vues.auth import define_auth_routes
define_auth_routes(app)

from Vues.student import student_routes
student_routes(app)

from Vues.formation import define_formation_endpoints
define_formation_endpoints(app)

@app.teardown_appcontext
def shutdown_session(e):
    db_session.remove()

#### Main, route
@app.route('/')
def main_app():
  return jsonify(
    success=True,
    path=request.path,
    method=request.method,
    query_string=request.query_string.decode('utf-8'),
    qs_data=request.args,
    form_data=request.form,
    json_form_data=request.json,
    attached_files=request.files
  )
