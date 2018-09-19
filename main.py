from flask import Flask, Response, request, render_template, session
from passlib.hash import bcrypt
from sqlitedb import database
import json,os

# Other project files
import login

# Initialise Flask App
app = Flask(__name__)
app.register_blueprint(login)
app.secret_key = os.urandom(24)

# Database file
dbfile = "booking.db"

@app.route('/')
@app.route('/index.html')
def home():
    if 'UUID' in session:
        return render_template('index.html', user="Test User")
    else:
        return render_template('login.html')

@app.route('/api')
def api(req=None):
    return json.dumps({})

@app.route('/register')
@login.route('/register.html')
def register():
    return render_template('register.html')

# API User authentication
@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    response,status  = doAuthenticate()
    return Response(json.dumps(response), status=status, mimetype="application/json")

def doAuthenticate():

    # User is already authenticated...
    if 'UUID' in session:
        return {    "authenticated":    True,
                    "redirect":         "/index.html" },200

    # Ensure data is of a valid type
    if request.content_type in ("application/json", "json"):
        req_data = request.get_json()
    #elif request.content_type == "text/plain":
        #req_data = request.args
    else:
        return {    "authenticated":    False,
                    "reason":           "Client Error: Data type must be application/json"    },400

    # Ensure we have the correct data.
    if 'email' in req_data and 'password' in req_data:
        email = req_data['email']
        password = req_data['password']
    else:                                       # Client did not provide email and password. 400 Bad Request.
        return {    "authenticated":    False,
                    "reason":           "Client Error: Must provide both email and password"    },400

    # Initialise the database object and fetch data from it.
    db = database(dbfile)
    user = db.getUserByEmail(email)
    db.close()

    # Only allow 5 tries.
    if user['incorrectTries'] == 5:        # User has run out of tries.
        return {    "authenticated":    False,
                    "reason":           "0 tries remaining.",
                    "triesRemaining":   0  },200    # Deny authentication for reason 0 tries remaining.

    # Check the user exists
    if not user:
        return {    "authenticated":    False,
                    "reason":           "User does not exist"   },200

    # Verify password...
    if bcrypt.verify(password, user['password']):
        session['UUID'] = user['UUID']
        return {    "authenticated":   True,    # Allow authenitcation and give location for AJAX redirect.
                    "redirect":        "/index.html"   },200

    print(f"Incorrect password was entered for user {user['email']}")

    # Password must be incorrect.
    print(user['incorrectTries'])
    tries = user['incorrectTries'] + 1                 # Append one to tries
    print(tries)
    db = database(dbfile)
    db.updateUserTriesByUUID(user['uuid'], tries)
    db.close()
    return {    "authenticated":        False,  # Deny authentication for reason incorrect password.
                "reason":               "Incorrect Password.",
                "triesRemaining":       5 - tries  },200


if __name__ == "__main__":
    app.run()