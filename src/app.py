import argparse
from server import app, db_session, clean_db, init_db, init_location, bcrypt
from helpers import get_settings_dict, write_settings_dict
import getpass

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, default=3501, help="Port")
parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
parser.add_argument("-i", "--init", help="Clean and re-init SQLite", action="store_true")
parser.add_argument("-l", "--locations", help="Refresh locations coordinates on startup", action="store_true")
parser.add_argument("--password", help="Define a new password for teachers", action="store_true")
parser.add_argument("-u", "--upgrade", help="Import a old database", default="")
parser.add_argument("--export", type=str, help="Export to file", default="")

program_args = parser.parse_args()

if program_args.init:
  print("Cleaning database")
  clean_db()
  print("Init tables")
  init_db()

if program_args.locations:
  print("Refreshing locations")
  init_location()

if program_args.export:
  from models_helpers import global_export
  global_export(program_args.export)

if program_args.upgrade:
  from models_helpers import import_legacy_db
  import_legacy_db(program_args.upgrade)

if program_args.password:
  psw1 = getpass.getpass(prompt='Saisissez un nouveau mot de passe: ', stream=None).strip()
  psw2 = getpass.getpass(prompt='Confirmez votre mot de passe: ', stream=None).strip()

  if psw1 != psw2:
    print("Les mots de passe ne correspondent pas. Abandon...")
    exit(1)

  new_hash = bcrypt.generate_password_hash(psw1)
  actual_settings = get_settings_dict()
  actual_settings['password'] = str(new_hash, encoding="utf-8")
  write_settings_dict(actual_settings)

  print("Le mot de passe a été mis à jour.")
  exit(0)

# Import all modules
import modules_main

# Run integrated Flask server
app.run(host='0.0.0.0', port=program_args.port, debug=program_args.debug)
