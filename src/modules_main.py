from flask import jsonify, request, Blueprint, send_from_directory
from flask_cors import CORS
from server import app, db_session
import os
from errors import ERRORS

if __name__ == "__main__":
  print("Please run app.py instead. This should not be the main file.")
  exit()

## Module initializer
#### Init modules
# Make app CORS-ready
CORS(app)

# Construct a blueprint to encapsulate API routes behind /api
bp = Blueprint('API', "promo-app-server")

# Init the login manager
from login_handler import set_app_login_manager
set_app_login_manager(app)

## Import the module and the apply function, and give app
# from Vues.get_student import get_student_routes
# get_student_routes(bp)

from errors import classic_errors
classic_errors(bp)

from Vues.auth import define_auth_routes
define_auth_routes(bp)

from Vues.student import student_routes
student_routes(bp)

from Vues.formation import define_formation_endpoints
define_formation_endpoints(bp)

from Vues.company import define_company_endpoints
define_company_endpoints(bp)

from Vues.domain import define_domain_endpoints
define_domain_endpoints(bp)

from Vues.contact import define_contact_endpoints
define_contact_endpoints(bp)

from Vues.internship import define_internship_endpoints
define_internship_endpoints(bp)

from Vues.job import define_job_endpoints
define_job_endpoints(bp)

from Vues.teacher import define_teacher_endpoints
define_teacher_endpoints(bp)

from Vues.ask_creation import define_ask_creation_routes
define_ask_creation_routes(bp)

# This should be after all bp definitions !
app.register_blueprint(bp, url_prefix='/api')

@app.teardown_appcontext
def shutdown_session(e):
    db_session.remove()


#### Serve the react app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
  if path != "" and os.path.exists(app.static_folder + '/' + path):
    # Serve the images/static css...
    return send_from_directory(app.static_folder, path)
  else:
    # Serve root
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def normal_404(err):
  if request.path.startswith('/api'):
    return ERRORS.PAGE_NOT_FOUND
  
  # Serve the react folder (404 is handled by React)
  return send_from_directory(app.static_folder, 'index.html')
