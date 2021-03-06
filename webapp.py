from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from flask_oauthlib.contrib.apps import github #import to make requests to GitHub's OAuth
from flask import render_template

import pprint
import os

import pymongo
import sys

app = Flask(__name__)

app.debug = False
#os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
  'github',
  consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
  consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
  request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
  base_url='https://api.github.com/',
  request_token_url=None,
  access_token_method='POST',
  access_token_url='https://github.com/login/oauth/access_token',  
  authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
  return {"logged_in":('github_token' in session)}

@app.route('/', methods=['GET'])
def home():
  return render_template('home.html')

@app.route('/posts', methods=['GET','POST'])
def blog():
  connection_string = os.environ["MONGO_CONNECTION_STRING"]
  db_name = os.environ["MONGO_DBNAME"]
  
  client = pymongo.MongoClient(connection_string)
  db = client[db_name]
  collection = db['forumPosts']
  
  docs = []

  for doc in collection.find():
    docs.append(doc)
  return render_template('posts.html', posts = docs)

@app.route('/login', methods=['POST'])
def login():
  return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))

@app.route('/logout', methods=['GET','POST'])
def logout():
  session.clear()
  return render_template('message.html', message='You sucessfully logged out')

@app.route('/myThreads', methods=['GET','POST'])
def myThreads():
  connection_string = os.environ["MONGO_CONNECTION_STRING"]
  db_name = os.environ["MONGO_DBNAME"]
  
  client = pymongo.MongoClient(connection_string)
  db = client[db_name]
  collection = db['forumPosts']
  
  myDocs = []
  
  if authorized(): #to check if logged in
    mine = {"user":('github_token' in session)}
    
    for doc in collection.find(mine):
      myDocs.append(doc)
      
    if len(myDocs) == 0: #is user hasn't posted yet
      message = "It seems you haven't posted any threads yet! You can post threads from the LINK TO PAGE page."
      status = "empty"
    else: #if user has posted
      message = "You've reached the bottom! Time to post something new!"
      status = "full"
      
  else: #if user is not logged in
    message = "It seems like you're not logged in! The login button can be found at the top right corner of any page"
    #maybe an arrow? that would be super cute
    status = "null"
    
  return render_template('myThreads.html', posts = myDocs, msg = message, stat = status)

                            
@app.route('/links', methods=['GET', 'POST'])
def links():
  return render_template('links.html')

@github.tokengetter
def get_github_oauth_token():
  return session['github_token']

@app.route('/login/authorized', methods=['POST'])
def authorized():
  resp = github.authorized_response()
  if resp is None:
    session.clear()
    message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
  else:
    try:
      session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
      session['user_data']=github.get('user').data
      #pprint.pprint(vars(github['/email']))
      #pprint.pprint(vars(github['api/2/accounts/profile/']))
      message='You were successfully logged in as ' + session['user_data']['login'] + '.'
    except Exception as inst:
      session.clear()
      print(inst)
      message='Unable to login, please try again.  '
  return render_template('message.html', message=message)

if __name__ == '__main__':
  app.run()
