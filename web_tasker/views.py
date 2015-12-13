# -*- coding: utf-8 -*-
from web_tasker import app, db, models
from flask import Flask, render_template, request, send_from_directory, request, make_response, session, redirect, url_for
from datetime import datetime

@app.route("/")
def index():
  # getting referer
  user_from='some-site.ru'

  if not logined_by_cookie():
    user=None
  else:
    user=check_user()

  return render_template('index.html', title='Hi', user_from=user_from, user=user) 

@app.route("/task")
@app.route("/task/<action>", methods=['GET', 'POST'])
def task(action='list'):
  #app.logger.info('Task begin '+str(check_user())) # debug
  if not logined_by_cookie():
    return redirect(url_for('login')) # if not logined go to login
  else:
    user_id = check_user()
  #app.logger.info('Task logined user:\t'+str(user_id)) # debug

  ### Showing task list
  if action == 'list' or action == 'list_closed':
    # rewrite to sqlalchemy like User.query.all() or User.query.filter() like in edit section
    # http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    if action == 'list_closed':
      task_status = False
      cur = db.session.execute("SELECT id, taskname, timestamp FROM task WHERE user_id='{}' AND status='Disabled'".format(user_id))
    else:
      task_status = True
      cur = db.session.execute("SELECT id, taskname, timestamp FROM task WHERE user_id='{}' AND status!='Disabled'".format(user_id))

    tasks = cur.fetchall()  
    return render_template('task.html', tittle='Задачи', user=get_nick(), task_list=tasks, task_status=task_status)

  ### Creating task
  elif action=='create':
    if request.method == 'POST':
      # Getting user id
      cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(get_nick()))
      user_id = cur.fetchone()[0]
      # Example of sqlAlchemy usage
      task_row = models.Task(user_id=user_id, taskname=request.form['taskname'], body=request.form['taskbody'], timestamp=datetime.now(), status='Active')
      db.session.add(task_row)
      db.session.commit()
      return redirect(url_for('task'))
    return render_template('task_create.html', tittle='Задачи', user=get_nick())

  ### Explain task 
  elif action=='view':
    task_id = request.args.get('id')
    cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(get_nick()))
    try: # if logined
      user_id = cur.fetchone()[0]
      cur = db.session.execute("SELECT taskname,body,timestamp FROM task WHERE id='{}' AND user_id='{}'".format(task_id, user_id))
      return render_template('task_view.html', tittle='Задачи', user=get_nick(), task_expl=cur.fetchone(), task_opened=task_id)
    except TypeError: return redirect(url_for('login')) # if not logined go to login
    return render_template('task_view.html', tittle='Задачи', user=get_nick(), task_expl=None)

  ### Edit task
  elif action=='edit':
    if request.method == 'POST':
      try:
        cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(get_nick()))
        user_id = cur.fetchone()[0]
        db.session.query(models.Task).filter_by(id=request.form['taskid']).update({'taskname':request.form['taskname'], 'status':request.form['taskstatus'], 'body':request.form['taskbody']})
        db.session.commit()
        return redirect(url_for('task'))
      except TypeError: return redirect(url_for('login'))
    else:
      task_edited = request.args.get('id')
      # Getting user id
      cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(get_nick()))
      try:
        user_id = cur.fetchone()[0]
        cur = db.session.execute("SELECT taskname,body,timestamp,status FROM task WHERE id='{}' AND user_id='{}'".format(task_edited, user_id))
        return render_template('task_modify.html', tittle='Задачи', user=get_nick(), task_edited=task_edited, task_expl=cur.fetchone())
      except TypeError: pass
      return render_template('task_modify.html', tittle='Задачи', user=get_nick(), task_edited=task_edited)

  return render_template('task.html', tittle='Задачи', user=get_nick())

@app.route("/profile")
def profile():

  if not logined_by_cookie():
    return redirect(url_for('login')) # if not logined go to login
  else:
    return render_template('profile.html', user=get_nick())
    
@app.route("/about")
def about():
    return render_template('about.html', tittle='О сайте')

@app.route("/login", methods=['GET', 'POST'])
def login():
  # need refactor
  if request.method == 'POST':
          
    user = str(request.form['username'])
    password = str(request.form['password'])
    
    if user and password:
      cur = db.session.execute("select id from user where nickname='{0}' and password='{1}'".format(user, password))
      user_id = int(cur.fetchone()[0])
      #app.logger.info(user_id) # debug
      
    else:
      return 'Try again'

    #if check_password:
    if user_id:
      # Set Cookies for knowing about user on other pages
      app.logger.info('Set cookies') # debug
      ### refactoring
      redirect_to_index = redirect(url_for('task'))
      response = app.make_response(redirect_to_index)
      
      #app.logger.info(response.headers) # debug
      #response.set_cookie('hash', str(auth_hash))
      response.set_cookie('id', value=str(user_id))
      response.set_cookie('pass', value=str(password))
      response.set_cookie('logged_at', value=str(datetime.now()))
      return response # need for set cookies finaly
    else:
      return 'login wrong'

  # if request.method == GET
  return render_template('login.html', user=None)

@app.route("/logout")
def logout():
  response = app.make_response(redirect(url_for('index')))
  response.set_cookie('id', value=' ', expires=1)
  response.set_cookie('pass', value=' ', expires=1)
  return response

@app.route("/register", methods=['GET', 'POST'])
def register_user():
  if request.method == 'POST':
  #if mail_exist(request.form.get('email'))
    return 'mail exist'
  #else
    import crypt;  
    salt = '$6$FIXEDS'
    pass_hash = crypt.crypt(request.form.get('password'), salt)
    app.logger.info('Generated hash:\t'+pass_hash) # debug
    user_row = models.User(nickname=request.form.get('username'),
			                     email=request.form.get('email'), 
                           password=request.form.get('password'),
                           p_hash=pass_hash,
                           role=models.ROLE_USER, register_date=datetime.now())
    db.session.add(user_row)
    db.session.commit()
    return redirect(url_for('index'))
  # if request.method == GET
  return render_template('register.html', user=None)

@app.route("/users")
def users_list():
  if not logined_by_cookie():
    return redirect(url_for('login')) # if not logined go to login
  else:
    user_id = check_user()

  cur = db.session.execute("select id,nickname,email from user")
  user_list = cur.fetchall()
  return render_template('user_list.html', user=get_nick(), user_list=user_list)

#############################################

def check_user():
  app.logger.info('Logined by cookies:\t'+str(logined_by_cookie())) # debug
  if logined_by_cookie():
    # refactoring
    return request.cookies.get('id')
  else:
    return None

def check_passwd(login, password):
  p_hash = get_hash(login)[0]
  if p_hash: # exist
    salt_end = p_hash.rindex('$')
    salt = p_hash[:salt_end]
    import crypt;
    crypted_pass_hash = crypt.crypt(password, salt)
    if crypted_pass_hash == p_hash:
      return 1
    else:
      #print("Login Failed: "+login, password)
      return 0
  else:
    #print("No user found: "+login)
    return 0

def logined_by_cookie():
  user_id = str(request.cookies.get('id'))
  #user_hash = request.cookies.get('hash')
  user_pass = str(request.cookies.get('pass'))
  #app.logger.info('UserID from cookie:\t'+user_id) # debug

  if not user_id == str('None'): # if user_id exist
    cur = db.session.execute("select id from user where id='{0}' and password='{1}'".format(user_id, user_pass))
    cookie = cur.fetchone()[0]
    #app.logger.info('UserID from db:\t\t'+str(cookie)) # debug
    
    if int(cookie) == int(user_id):
      return True # yeah LOGINED
    
  return False

def get_nick():
  user_id = request.cookies.get('id')
  if user_id:
    cur = db.session.execute("SELECT nickname FROM user WHERE id='{0}'".format(int(user_id)))
    return cur.fetchone()[0]

  return None

def get_hash(username):
  cur = db.session.execute("SELECT p_hash FROM user WHERE nickname='{0}'".format(username))
  return cur.fetchone()