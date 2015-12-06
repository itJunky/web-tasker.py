# -*- coding: utf-8 -*-
from web_tasker import app
from flask import Flask, render_template, request, send_from_directory, request, session, redirect, url_for

sessions = {'username': 'tester'}
user = None

@app.route("/")
def index():
  # getting referer
  user_from='some-site.ru'
  if 'username' in sessions:
    user=sessions['username']
  else:
    user=None

  return render_template('index.html', title='Hi', user_from=user_from, user=user) 

@app.route("/task")
@app.route("/task/<number>")
def task(number=None):
  return render_template('task.html', tittle='Задачи', number=number, user=user)

@app.route("/profile")
def profile():
  global user
  #return str(user)
  return render_template('profile.html', user=user)

@app.route("/about")
def about():
    return render_template('about.html', tittle='О сайте')

@app.route("/login", methods=['GET', 'POST'])
def login():
  # need refactor
  global user
  if request.method == 'POST':
    sessions['username'] = request.form['username']
    user = sessions['username']
    #return str(user)
    return redirect(url_for('profile'))
  # if request.method == GET
  return render_template('login.html', user=None)

@app.route("/logout")
def logout():
  sessions.pop('username', None)
  return redirect(url_for('index'))
