# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, send_from_directory, request, make_response, session, redirect, url_for
# for custom HTTP statuses
#from flask.ext.api import status 
HTTP_403_FORBIDDEN = 403
from datetime import datetime

import logging

from web_tasker import app, db
from web_tasker.models import *

@app.route("/")
def index():
  # getting referer
  user_from='some-site.ru'

  if not logined_by_cookie():
    user=None
  else:
    user=get_user_id()

  return render_template('index.html', title='Hi', user_from=user_from, user=user) 

###########################
########## TASK ###########
###########################
@app.route("/task")
@app.route("/task/<action>", methods=['GET', 'POST'])
def task(action='list'):
  if not logined_by_cookie():
    app.logger.error('Not logined') # debug
    return redirect(url_for('do_login')) # if not logined go to login
  else:
    user_id = get_user_id()
  # app.logger.info('Task viewing by user:\t'+str(user_id)) # debug

  ### Showing task list
  # Need:
  #       User ID (upper)
  #       Project ID
  #       Project Name (SQL)
  #       Parent ID (SQL)
  #       Depth in tree (SQL)
  if action == 'list' or action == 'list_closed':
    project_id = request.args.get('project_id')
    app.logger.info('Project ID is:\t'+str(project_id)) # debug
    if project_id == None: # if no id in form try cookie, because it from last session
      project_id = request.cookies.get('project_id')
      if project_id == None: # if no id in cookie, get least of all user's projects
        project_id = get_first_project_id(user_id)

    # rewrite to sqlalchemy like User.query.all() or User.query.filter() like in edit section
    # http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    if action == 'list_closed':
      task_status = False # for taskmenu
      cur = db.session.execute("SELECT id, taskname, timestamp, parent_id, depth FROM task WHERE status='Disabled' AND depth=0 AND user_id='{}' AND project_id='{}'".format(user_id, project_id))
    else: # Show opened tasks
      task_status = True # for taskmenu
      # Get deepest depth
      cur = db.session.execute("SELECT MAX(depth) \
                                FROM task \
                                WHERE status!='Disabled' \
                                  AND user_id='{}' \
                                  AND project_id='{}'".format(user_id, project_id))
      max_depth = cur.fetchone()[0]
      if max_depth is None: return render_template('task.html', title=u'Задачи', user=get_nick(), task_list=[], task_status=task_status)
      app.logger.debug('Max depth:\t'+str(max_depth)) # debug
      tasks = []
      # Get named list from db query
      for depth in xrange(0,max_depth+1):
        cur = db.session.execute("SELECT id, taskname, timestamp, parent_id, depth \
                                  FROM task \
                                  WHERE status!='Disabled' \
                                    AND depth='{}' \
                                    AND user_id='{}' \
                                    AND project_id='{}'".format(depth, user_id, project_id))
        tasks_tmp = cur.fetchall()
        for t in tasks_tmp:
          tasks.append(t)

    #tasks = cur.fetchall() 

      # sort by tree
      sorted_list = []
      tasks = QuickSort(tasks, 0, sorted_list)
      app.logger.debug('Tasks is:\n'+str(tasks)) # debug

    tasks = remove_microseconds(tasks)
    return render_template('task.html', title=u'Задачи', user=get_nick(), task_list=tasks, task_status=task_status)

  ### Creating task
  elif action=='create':
    if request.method == 'POST':
      # Getting user id
      cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(get_nick()))
      user_id = cur.fetchone()[0]
      project_id = request.cookies.get('project_id')
      cur = db.session.execute("SELECT depth FROM task WHERE id='{}'".format(request.form['taskparent']))
      try:
        parent_depth = cur.fetchone()[0]
      except TypeError:
        parent_depth = -1
      # Example of sqlAlchemy usage
      task_row = Task(user_id=user_id,
                      project_id=project_id,
                      taskname=request.form['taskname'],
                      body=request.form['taskbody'],
                      parent_id=request.form['taskparent'],
                      timestamp=datetime.now(),
                      depth=int(parent_depth)+1,
                      status='Active')
      db.session.add(task_row)
      db.session.commit()
      return redirect(url_for('task', action='list', project_id=project_id))
    return render_template('task_create.html', title=u'Задачи', user=get_nick())

  ### Explain task 
  elif action=='view':
    task_id = request.args.get('id')
    app.logger.debug('### Start viewing {} ###'.format(task_id))
    nickname = get_nick()
    cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(nickname))
    try: # if logined
      user_id = cur.fetchone()[0]
      task_explained = db.session.execute("SELECT taskname,body,timestamp FROM task WHERE id='{}' AND user_id='{}'".format(task_id, user_id))
      all_comments = db.session.execute("SELECT c.id,c.user_id,c.timestamp,c.text,u.nickname FROM comment c, user u WHERE c.task_id='{}' and c.user_id=u.id".format(task_id))
      #all_comments = db.session.query(Comment).filter_by(task_id=task_id).all()
      app.logger.debug('### End viewing ###')
      # may be need redirect to internal func here
      return render_template('task_view.html', title=u'Задачи', user=nickname,
                              task_expl=task_explained.fetchone(), task_opened=task_id,
                              comments=all_comments.fetchall())
    except TypeError: # if not logined go to login
      return redirect(url_for('do_login'))
    else:
      return 'Unresolved error'

  ### Edit task
  elif action=='edit':
    nickname = get_nick()
    if request.method == 'GET':
      task_edited = request.args.get('id')
      # Getting user id
      cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(nickname))
      try:
        user_id = cur.fetchone()[0]
        # Getting task by user and task id
        cur = db.session.execute("SELECT taskname,body,timestamp,status,parent_id \
                                  FROM task \
                                  WHERE id='{}' AND user_id='{}'".format(task_edited, user_id))
        return render_template('task_modify.html', title=u'Задачи', user=nickname, task_edited=task_edited, task_expl=cur.fetchone())
      except TypeError: pass
      return render_template('task_modify.html', title=u'Задачи', user=nickname, task_edited=task_edited)
    elif request.method == 'POST':
      try:
        cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(nickname))
        user_id = cur.fetchone()[0]
      except TypeError: return redirect(url_for('do_login'))

      parent_id = request.form['taskparent']
      app.logger.info('### PARENT ID: '+str(parent_id)) # debug

      cur = db.session.execute("SELECT depth FROM task WHERE id='{}'".format(parent_id))
      try:
        parent_depth = cur.fetchone()[0]
      except TypeError:
        parent_depth = -1
      app.logger.info('### PARENT DEPTH: '+str(parent_depth)) # debug
      # parent_depth = 1

      db.session.query(Task).filter_by(id=request.form['taskid']).update({
                'taskname':request.form['taskname'],
                'status':request.form['taskstatus'],
                'body':request.form['taskbody'],
                'parent_id':parent_id,
                'depth':parent_depth+1 })
      db.session.commit()
      return redirect(url_for('task'))

  return 'Unresolved error 2'


@app.route("/comment_to_task", methods=['POST'])
def post_comment_to_task():
  app.logger.info('### Post Comment to db ###') # debug
  new_comment = Comment(user_id=get_user_id(), task_id=request.form['taskid'], timestamp=datetime.now(), text=request.form.get('commenttext'))
  db.session.add(new_comment)
  db.session.commit()
  return redirect(url_for('task', action='view', id=int(request.form['taskid'])))

###########################
######### PROJECT #########
###########################
@app.route("/project")
@app.route("/project/<action>", methods=['GET', 'POST'])
def project(action='list'):
  if not logined_by_cookie():
    app.logger.error('Not logined') # debug
    return redirect(url_for('do_login')) # if not logined go to login
  else:
    user_id = get_user_id()

  app.logger.info(' ### Project logined user ID:\t'+str(user_id)) # debug

  ### Show Project List ###
  if action == 'list' or action == 'list_closed':
    if action == 'list_closed':
      project_status = False
      project_ids = get_projects_for_user(user_id, 'Disabled')
    else:
      project_status = True
      project_ids = get_projects_for_user(user_id, 'Active')

    app.logger.debug('project_ids: '+str(project_ids)) # debug
    if project_ids:
      projects = []
      for project_id in project_ids:
        project_name = db.session.query(Project.name).filter_by(id=project_id[0]).all()[0]
        projects.append([project_id[0], project_name[0]])
        # app.logger.debug('project_id is: '+str(project_id[0])+' name is '+str(project_name)) # debug
    return render_template('project.html', title=u'Проекты', user=get_nick(), project_list=projects, project_status=project_status)

  ### Create new Project ###
  elif action == 'create':
    user_id = get_user_id()
    if request.method == 'POST':
      # Need:
      #       User ID (upper)
      #       Project Name
      #       Project ID
      project_name = request.form.get('projectname')

      db.session.add(Project(name=project_name))
      db.session.commit()
      project_id = db.session.query(Project.id).filter_by(name=project_name)
      db.session.add(Project_association(user_id=user_id, project_id=project_id[0][0]))
      db.session.commit()
      return redirect(url_for('project')) # got to project list

    else: # if GET request
      return render_template('project_create.html', title=u'Проекты', user=get_nick(), user_id=user_id)

  ### View Project ###
  elif action == 'view':
    project_id = str(request.args.get('id'))
    app.logger.debug('Project ID for view: '+str(project_id)) # debug
    response = app.make_response(redirect(url_for('task', action='list', project_id=project_id)))
    response.set_cookie('project_id', value=project_id)
    return response # go to task list with cookie 'project_id' set

  ### Edit Project ###
  elif action == 'edit':
    project_id = request.args.get('id')
    if request.method == 'POST':
      project_name = request.form.get('projectname')
      db.session.query(Project).filter_by(id=project_id).update({
                'name':project_name,
                'status':'Active',
                'owner': user_id})
      db.session.commit()
      return redirect(url_for('project', action='list', project_id=project_id))
    else: # if GET request
      # Need:
      #       Project ID
      #       Project Name
      #       Project Users
      project_name = db.session.query(Project.name).filter_by(id=project_id).all()[0]
      project_user_ids = db.session.query(Project_association.user_id).filter_by(project_id=project_id).all()
      project_user_names = []
      for user_id in project_user_ids:
        name = db.session.query(User.nickname).filter_by(id=user_id[0]).all()[0]
        project_user_names.append(name[0])

      app.logger.debug('### Project # Edit ### id from form: '+str(project_id[0])+'\n'+ \
                        'Name: '+str(project_name)+'\n'+ \
                        'User IDs: '+str(project_user_ids)+'\n'+ \
                        'Users in project: '+str(project_user_names) ) # debug
      project_full_data = [project_id, project_name[0], project_user_ids, project_user_names]
      return render_template('project_edit.html', title=u'Проекты', user=get_nick(), project=project_full_data)


@app.route("/profile")
def profile():
  if not logined_by_cookie():
    return redirect(url_for('do_login')) # if not logined go to login
  else:
    return render_template('profile.html', user=get_nick())
    

@app.route("/about")
def about():
    return render_template('about.html', title=u'О сайте')


@app.route("/login", methods=['GET', 'POST'])
def do_login():
  if request.method == 'POST':
    user = str(request.form['username'])
    password = str(request.form['password'])
    
    #app.logger.info('Check password:\t'+str(check_passwd(user, password))) # debug
    if check_passwd(user, password):
      # Set Cookies for knowing about user on other pages
      auth_hash = str(id_generator())
      user_id = int(get_user_id_from_db(user))
      app.logger.debug('Set cookies '+str(user)+' '+str(user_id)+' '+auth_hash) # debug
      
      response = app.make_response(redirect(url_for('index')))
      response.set_cookie('id', value=str(user_id))
      response.set_cookie('hash', value=auth_hash)
      response.set_cookie('logged_at', value=str(datetime.now()))
      db.session.query(User).filter_by(id=user_id).update({'cookie':auth_hash})
      db.session.commit()
      #sql = "UPDATE user SET cookie='{}' WHERE id='{}'".format(auth_hash, user_id)
      #app.logger.info('SQL:\t'+str(sql)) # debug
      #db.session.execute(sql)
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
    if mail_exist(request.form.get('email')):
      return 'mail exist'
    else:
      # Prepare user data to insert in db
      import crypt;
      salt = '$6$FIXEDS'
      pass_hash = crypt.crypt(request.form.get('password'), salt)
      user_row = User(nickname=request.form.get('username'),
                      email=request.form.get('email'), 
                      password=request.form.get('password'),
                      p_hash=pass_hash,
                      role=ROLE_USER,
                      register_date=datetime.now())
      app.logger.info('Registered user:\n'+
                      request.form.get('username')+'\n'+
                      request.form.get('email')+'\n'+
                      pass_hash+'\n') # debug
      db.session.add(user_row)
      db.session.commit()

      # Getting id of new user for project owner
      user_id = db.session.query(User.id).filter_by(email=request.form.get('email')).all()[0][0]
      app.logger.info('NEW USER ID:\t'+str(user_id)) # debug
      # Prepare empty project for user
      new_project = Project(name=u'Добро пожаловать',
                            status='Active',
                            owner=user_id)
      db.session.add(new_project)
      db.session.commit()

      # Getting Greet project id for assign task
      new_project_id = db.session.query(Project.id).filter_by(name=u'Добро пожаловать').filter_by(owner=user_id).all()[0][0]
      # Creating user association to project
      new_assoc = Project_association(user_id=user_id, project_id=new_project_id)
      db.session.add(new_assoc)
      db.session.commit()

      # Setting Greet task
      task_row = Task(taskname=u"Это Ваша первая задача",
                      parent_id=0,
                      body=u"Вы можете создавать другие задачи в рамках проекта и делиться проектами с другими пользователями",
                      timestamp=datetime.now(),
                      user_id=user_id,
                      project_id=new_project_id,
                      status='Active',
                      depth=0)
      db.session.add(task_row)
      db.session.commit()

      return redirect(url_for('index'))

  if request.method == 'GET':
    return render_template('register.html', user=None)


@app.route("/users")
def users_list():
  if not logined_by_cookie():
    return redirect(url_for('do_login')) # if not logined go to login
  else:
    user_id = get_user_id()

  cur = db.session.execute("select id,nickname,email from user")
  user_list = cur.fetchall()
  return render_template('user_list.html', user=get_nick(), user_list=user_list)

#############################################

def get_user_id():
  if logined_by_cookie():
    # refactoring
    user_id = request.cookies.get('id')
    # app.logger.info('Logined by cookies:\t'+str(user_id)) # debug
    return int(user_id)
  else:
    return None


def mail_exist(email):
  cur = db.session.execute("SELECT email FROM user")
  all_emails = cur.fetchall()
  if email in all_emails:
    app.logger.info('### Email exist in database ###') # debug
    return True
  else:
    app.logger.info('### Email doesn\'t exist in database ###') # debug
    return False


def get_user_id_from_db(username):
    cur = db.session.execute("SELECT id FROM user WHERE nickname='{0}'".format(str(username)))
    return cur.fetchone()[0]


def check_passwd(login, password):
  db_hash = get_hash_from_db(login)[0]
  if db_hash: # exist
    salt_end = db_hash.rindex('$')
    salt = db_hash[:salt_end]
    import crypt;
    crypted_pass_hash = crypt.crypt(password, salt)
    if crypted_pass_hash == db_hash:
      return 1 # Passwords equal
    else:
      return 0 # Not equal
  else:
    return 0 # p_hash doesn't exist


def logined_by_cookie():
  user_id = str(request.cookies.get('id'))
  user_hash = request.cookies.get('hash')
  if user_hash:
    app.logger.debug('UserID from cookie:\t'+user_id+' '+user_hash) # debug

    if not user_id == str('None'): # if user_id exist
      cur = db.session.execute("SELECT cookie FROM user WHERE id='{0}'".format(user_id))
      cookie = cur.fetchone()[0] # getting hash
      # app.logger.debug('Cookie from db:\t\t'+str(cookie)) # debug

      if str(cookie) == str(user_hash):
        return True # yeah LOGINED
    
  return False


def get_nick():
  user_id = request.cookies.get('id')
  if user_id:
    cur = db.session.execute("SELECT nickname FROM user WHERE id='{0}'".format(int(user_id)))
    return cur.fetchone()[0]

  return None


def get_hash_from_db(username):
  cur = db.session.execute("SELECT p_hash FROM user WHERE nickname='{0}'".format(username))
  return cur.fetchone()

def get_projects_for_user(user_id, status='Active'):
  if status == 'Disabled':
    project_status = False
    cur = db.session.execute("SELECT id FROM project WHERE status='Disabled' and value='{}'".format(user_id))
    project_ids = cur.fetchall()[0]
  else:
    project_status = True
    project_ids = db.session.query(Project_association.project_id).filter_by(user_id=user_id)

  return project_ids

def get_first_project_id(user_id):
  return 1

import string
def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    import random
    return ''.join(random.choice(chars) for _ in range(size))

def QuickSort(lst, parent_id, sorteded):
  sorted_list = sorteded
  for eid, taskname, date, parent, depth in lst:
    if parent == parent_id:
      element = {'id': eid, 'name': taskname, 'date': date, 'parent': parent, 'depth': depth}
      sorted_list.append(element)
      t = QuickSort(lst, eid, sorted_list)

  return sorted_list

def remove_microseconds(tasks):
  tasks_short_date = []
  for task in tasks:
    tasks_short_date.append([task['id'],
                             task['name'],
                             task['date'].split(".")[0],
                             task['parent'],
                             task['depth']])

  tasks = tasks_short_date
  # for task in tasks:
  #   app.logger.debug('Task preview:\t'+str(task)) # debug
  return tasks
