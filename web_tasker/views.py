# -*- coding: utf-8 -*-
from web_tasker import app, db, models
from flask import Flask, render_template, request, send_from_directory, request, session, redirect, url_for
import datetime

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
    user = str(sessions['username'])
    password = str(request.form['password'])
    if user or password:
      cur = db.session.execute("select id from user where nickname='{0}' and password='{1}'".format(user, password))
    else:
      return 'Try again'
    if cur.fetchone():
      return redirect(url_for('profile'))
    else:
      return 'login wrong'
  # if request.method == GET
  return render_template('login.html', user=None)

@app.route("/logout")
def logout():
  sessions.pop('username', None)
  return redirect(url_for('index'))

@app.route("/register", methods=['GET', 'POST'])
def register_user():
  if request.method == 'POST':
    user_row = models.User(nickname=request.form['username'], email=request.form['email'], password=request.form['password'], role=models.ROLE_USER, register_date=datetime.datetime.now())
    db.session.add(user_row)
    db.session.commit()
    return redirect(url_for('index'))
  # if request.method == GET
  return render_template('register.html', user=None)

@app.route("/users")
def users_list():
  cur = db.session.execute("select id,nickname,email from user")
  user_list = cur.fetchall()
  return render_template('user_list.html', user=user, user_list=user_list)
