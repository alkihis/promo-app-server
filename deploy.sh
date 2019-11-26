python3 -m venv .envs
source .envs/bin/activate
pip install flask flask-cors sqlalchemy flask_login blinker timestring python-Levenshtein requests

## Ready
echo "Virtual env is ready."
echo "Enter 'source .envs/bin/activate' to enter venv."
echo "Activate server with python src/app.py"
