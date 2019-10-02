from flask import Flask, jsonify, g
from flask_cors import CORS
import argparse
from helpers import getRequest
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=3501, help="Port")
parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")

program_args = parser.parse_args()

app = Flask("promo-app-server")
CORS(app)

### Connect/disconnect to database
@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
      db.close()

#### Init modules
## Import the module and the apply function, and give app
from get_student import get_student_routes
get_student_routes(app)

from errors import classic_errors
classic_errors(app)

#### Main, route
@app.route('/')
def main_app():
  request = getRequest()

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
