python3 -m venv .envs
source .envs/bin/activate
pip install flask flask-cors sqlalchemy flask_login blinker timestring python-Levenshtein requests flask_bcrypt
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

## Ready
echo "Virtual env is ready."
echo "Enter 'source .envs/bin/activate' to enter venv."
echo "Activate server with python src/app.py"
