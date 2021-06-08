from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os
import traceback
import urllib.request
import json
import random
import datetime

from sqlalchemy.orm import sessionmaker
from register import User as U
from register import Grade, return_sqlalchemysession
from passhasher import hash_string_sha
from pogoda import pobierzpogode

#imports for OAuth to work
import webbrowser
import sqlite3
import requests
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
# Internal imports
from db import init_db_command
from user import User

# Google OAuth Login Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# lokalizacja widoków i elementów statycznych
app = Flask(
  __name__,
  template_folder='templates',
  static_folder='static',
  )
#used by this app to cryptographically sign cookies etc.
app.secret_key = os.urandom(12)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)
# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
    
# google
@app.route("/")
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return render_template('logowanie.html')
# google    
@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))    
###
# default login and logut with sqlalchemy etc.
###
@app.route('/home')
def home():
  if not session.get('logged_in'):
    return render_template('logowanie.html')
  else:
    return render_template('frontpage.html')
@app.route('/zaloguj', methods=["POST"])
def zaloguj_uzytkownika():
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])

    #Stworz obiekt sesji SQLalchemy (ORM)
    sqlsession = return_sqlalchemysession()

    # Zadaj zapytanie w sposob bezpieczny
    # od sqlinjection
    query = sqlsession.query(U).filter(U.username.in_([POST_USERNAME]))

    #wez 1 uzytkownika z takim nickiem (zakladamy ze nie ma powtorek)
    user = query.first()
    try:
      #Ta linia musi być w try, bo jeżeli nie ma usera (user==None) to nie zadziała user.check_password
      logged = user.check_password(POST_PASSWORD)
      # check_password zwraca True jak haslo sie zgadza
      if logged:
        session['logged_in'] = True
        
      else:
        # Jak działa flash: https://flask.palletsprojects.com/en/1.1.x/patterns/flashing/
        flash('No user or wrong password provided')
        return render_template('logowanie.html')
    except AttributeError as e:
      flash('No user or wrong password provided')
      #traceback trick to printout the error despite the except
      print(traceback.format_exc())
    return home()


@app.route('/wyloguj')
def wyloguj():
  session['logged_in'] = False
  return "Wylogowano" 

@app.route('/register', methods=['POST', 'GET'])
def do_register():
  POST_USERNAME = str(request.form['username'])
  POST_PASSWORD = str(request.form['password'])
  
  sqlsession = return_sqlalchemysession()
  user = U(POST_USERNAME,POST_PASSWORD)

  sqlsession.add(user)
  sqlsession.commit()
  sqlsession.close()
  return home()

@app.route('/signup', methods=["GET"])
def return_registrationpage():
  return render_template('signup.html')

@app.route("/pogoda")
def pokazpogode():
  temp,humid,weathertype,rain = pobierzpogode()
  return render_template("pogoda.html", temp=temp, humid=humid,weathertype=weathertype, rain=rain)

# Propozycja dodatkowego zadania - bootstrap? 
# Przyjrzyj sie temu jak dobrze wyglada ta strona w html
@app.route("/bootstrap")
def bootstrap():
  return render_template('bootstrap.html')

# DODATKOWA FUNKCJA - WYSWIETLANIE LISTY ELEMENTOW W JINJA 2 - oceny
@app.route('/grades', methods=['GET'])
def return_grades():
  #ponizszy kod aby dostepne bylo tylko dla zalogowanych
  # if not session.get('logged_in'):
    # return render_template('login.html')
  # else:
    sqlsession = return_sqlalchemysession()
    grades = sqlsession.query(Grade).all()
    # for x in grades:
      # print ({i.name: getattr(x, i.name) for i in x.__table__.columns})
    return render_template("grades.html", grades=grades)

## Dodawanie nowych ocen (patrz na dol tabelki)
@app.route('/addgrade', methods=['GET'])
def grades():
  # if not session.get('logged_in'):
    # return render_template('login.html')
  # else:
    gradeval = random.choice(['2', '3', '3.5', '4', '4.5', '5'])
    user_id = 99
    added_date = datetime.date.today()
    grade = Grade(gradeval, added_date, user_id)
    sqlsession = return_sqlalchemysession()
    sqlsession.add(grade)
    sqlsession.commit()
    return return_grades()

## Dodatkowa metoda hashowania
@app.route('/hash/<string:test>', methods = ['GET', 'POST'])
def testhash(test):
  return hash_string_sha(test)

@app.route('/terms', methods = ['GET', 'POST'])
def terms():
  return webbrowser.open_new_tab("https://replit.com/site/terms", code=302)

@app.route('/privacy', methods = ['GET', 'POST'])
def privacy():
  return webbrowser.open_new_tab("https://replit.com/site/privacy", code=302)  

#if __name__ == "__main__":
#  app.run(
#    host='0.0.0.0', 
#    port=8080, debug=True)