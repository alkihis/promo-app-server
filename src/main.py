from flask import jsonify
from flask_cors import CORS
import argparse
from helpers import get_request, clean_db
from server import app, db_session, init_db

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=3501, help="Port")
parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
parser.add_argument("-i", "--init", help="Clean and re-init SQLite", action="store_true")

program_args = parser.parse_args()
CORS(app)

#### Init modules
## Import the module and the apply function, and give app
from get_student import get_student_routes
get_student_routes(app)

from errors import classic_errors
classic_errors(app)

if program_args.init:
  print("Cleaning database")
  clean_db()
  print("Init tables")
  init_db()

@app.teardown_appcontext
def shutdown_session(e):
    db_session.remove()

#### Main, route
@app.route('/')
def main_app():
  request = get_request()

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

# Run integrated Flask server
app.run(host='0.0.0.0', port=program_args.port, debug=program_args.debug)
