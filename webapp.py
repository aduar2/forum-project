import os
from flask import Flask, url_for, render_template, request
from flask import redirect
from flask import session

app = Flask(__name_)

@app.route('/')
def home ()
  return render_template('home.html')

@app.route('/posts')
def blog()
  return render_template('posts.html')

@app.route('/login')
def login()
  return github.authorize(callback=url_for('authorized', _external=True, _scheme='https'))

@app.route('/logout')
def logout()
  session.clear()
  return render_template('message.html', message='You sucessfully logged out')
