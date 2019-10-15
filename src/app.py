import argparse
from server import app, db_session, clean_db, init_db

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=3501, help="Port")
parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
parser.add_argument("-i", "--init", help="Clean and re-init SQLite", action="store_true")

program_args = parser.parse_args()

if program_args.init:
  print("Cleaning database")
  clean_db()
  print("Init tables")
  init_db()

# Import all modules
import modules_main

# Run integrated Flask server
app.run(host='0.0.0.0', port=program_args.port, debug=program_args.debug)
