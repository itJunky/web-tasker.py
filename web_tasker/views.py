# -*- coding: utf-8 -*-

import string
from flask import render_template, request, redirect, url_for
from datetime import datetime

from web_tasker import app
from web_tasker.models import db, User, Task, ProjectAssociation, Comment, Project, ROLE_USER

# for custom HTTP statuses
HTTP_403_FORBIDDEN = 403


@app.route("/")
def index():
    # getting referer
    user_from = 'some-site.ru'

    if not logined_by_cookie():
        user = None
    else:
        user = get_user_id()

    return render_template('index.html', title='Hi', user_from=user_from, user=user)


###########################
########## TASK ###########
###########################
@app.route("/task")
@app.route("/task/<action>", methods=['GET', 'POST'])
def task(action='list'):
    try:
        user_id = get_user_id()
        app.logger.info('Some task viewing by user:\t' + str(user_id))  # debug
        if user_id == None: return redirect(url_for('do_login'))  # if not logined go to login
    except:
        app.logger.error('Not logined')  # debug
        return redirect(url_for('do_login'))  # if not logined go to login

    ### Show task list
    if action == 'list' or action == 'list_closed':
        ### Showing task list
        # Need:
        #       User ID (upper)
        #       Project ID
        #       Project Name (SQL)
        #       Parent ID (SQL)
        #       Depth in tree (SQL)
        project_id = request.args.get('project_id')
        app.logger.info('Project ID is:\t' + str(project_id))  # debug
        if project_id == None:  # if no id in form try cookie, because it from last session
            project_id = request.cookies.get('project_id')
            app.logger.debug("!!! TRYING TO GET PROJECT ID !!!\nFrom cookie: " + str(project_id))
            if project_id == None:  # if no id in cookie, get least of all user's projects
                app.logger.debug("!!! TRYING TO GET PROJECT ID !!!\nFirst from all: " + str(project_id))
                project_id = get_first_project_id(user_id)

        # Check access to project
        try:
            check_up = db.session.query(ProjectAssociation.id).\
                filter_by(project_id=project_id, user_id=user_id).one()
        except:
            return "Wrong project ID"

        tasks = []
        if action == 'list_closed':  # show all tasks
            task_status = False  # for taskmenu
            tasks = Task.query.filter(Task.user_id == user_id, Task.project_id == project_id).all()

        else:  # Show opened tasks only
            task_status = True  # for taskmenu
            tasks = Task.query.filter(Task.user_id == user_id, Task.project_id == project_id).filter(
                Task.status == 'Active').all()

        # Get project name
        project_name = db.session.query(Project.name).filter_by(id=project_id).one()[0]

        app.logger.debug('Tasks is:\n' + str(tasks))  # debug
        # tasks = order_tasks(tasks, 0, [])
        return render_template('task/list.html', title=u'Задачи', user=get_nick(), task_list=tasks,
                               task_status=task_status, project_name=project_name)

    ### Creating task
    elif action == 'create':
        parent_id = request.args.get('taskparent')
        app.logger.info('PARENT TASK ID from args:\t' + str(parent_id))  # debug
        if parent_id is None:
            parent_id = request.form['taskparent']
            app.logger.info('PARENT TASK ID from form:\t' + str(parent_id))  # debug
            if parent_id is None:
                parent_id = 0
                app.logger.info('PARENT TASK ID is ZERO:\t' + str(parent_id))  # debug

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
                            parent_id=parent_id,
                            timestamp=datetime.now(),
                            depth=int(parent_depth) + 1,
                            status='Active')
            db.session.add(task_row)
            db.session.commit()
            return redirect(url_for('task', action='list', project_id=project_id))
        return render_template('task/create.html', title=u'Задачи', user=get_nick(), parent=parent_id)

    ### Explain task
    elif action == 'view':
        task_id = request.args.get('id')
        app.logger.debug('### Start viewing task id: {} ###'.format(task_id))

        try:
            nickname = get_nick()
        except:
            app.logger.debug('Nick is wrong: ' + nickname)
            return "error", 500
            # return redirect(url_for('do_login')) # if not logined go to login
        else:
            app.logger.debug('Nick is ok: ' + nickname)

        try:  # if logined
            user_id = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(nickname)).fetchone()[0]
            app.logger.debug('UserID is: ' + str(user_id))
        except TypeError:  # if not logined go to login
            app.logger.debug("Login is wrong")
            return redirect(url_for('do_login'))

        if permit_to_project(user_id, task_id):
            task_explained = db.session.execute(
                "SELECT taskname,body,timestamp FROM task WHERE id='{}'".format(task_id))
            all_comments = db.session.execute(
                "SELECT id,user_id,timestamp,text FROM comment c WHERE task_id='{}'".format(task_id)).fetchall()
            all_comments = convert_id_to_nick(all_comments)
        else:
            return "Access to this task is denied for you"

        app.logger.debug('### End viewing ###')
        # may be need redirect to internal func here
        return render_template('task/view.html', title=u'Задачи', user=nickname,
                               task_expl=task_explained.fetchone(), task_opened=task_id,
                               comments=all_comments)

    ### Edit task
    elif action == 'edit':
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
                return render_template('task/edit.html', title=u'Задачи', user=nickname, task_edited=task_edited,
                                       task_expl=cur.fetchone())
            except TypeError:
                pass
            return render_template('task/edit.html', title=u'Задачи', user=nickname, task_edited=task_edited)
        elif request.method == 'POST':
            try:
                cur = db.session.execute("SELECT id FROM user WHERE nickname='{}'".format(nickname))
                user_id = cur.fetchone()[0]
            except TypeError:
                return redirect(url_for('do_login'))

            parent_id = request.form['taskparent']
            app.logger.info('### PARENT ID: ' + str(parent_id))  # debug

            cur = db.session.execute("SELECT depth FROM task WHERE id='{}'".format(parent_id))
            try:
                parent_depth = cur.fetchone()[0]
            except TypeError:
                parent_depth = -1
            app.logger.info('### PARENT DEPTH: ' + str(parent_depth))  # debug
            # parent_depth = 1

            db.session.query(Task).filter_by(id=request.form['taskid']).update({
                'taskname': request.form['taskname'],
                'status': request.form['taskstatus'],
                'body': request.form['taskbody'],
                'parent_id': parent_id,
                'depth': parent_depth + 1})
            db.session.commit()
            return redirect(url_for('task'))

    ### Delete task
    elif action == 'delete':
        task_to_delete = request.args.get('id')
        db.session.execute("DELETE FROM task WHERE id={}".format(task_to_delete))
        db.session.commit()
        app.logger.info("### DELETING TASK ###\nTask to delete: " + str(task_to_delete))
        return redirect(url_for('task'))

    return 'Unresolved error 2 in task'


@app.route("/comment_to_task", methods=['GET', 'POST'])
def post_comment_to_task():
    if request.method == 'GET':
        user_id = get_user_id()
        if user_id is None:
            return redirect(url_for('do_login'))  # if not logined go to login
        comment_id = request.args.get('id')
        what_to_do = request.args.get('do')
        if what_to_do == 'delete':
            author_id = get_comment_author_id(comment_id)
            if author_id == user_id:
                res = "USER_ID: %s\nCOMMENT_ID: %s\nAUTHOR_ID: %s\nWhat_To_Do: %s" % (
                    user_id, comment_id, author_id, what_to_do)
                print(res)
                db.session.query(Comment).filter_by(id=comment_id).delete()
                db.session.commit()
                return redirect(url_for('task', action='view', id=int(request.args.get('tid'))))
            else:
                return "You can delete comment only if you is it author."

    if request.method == 'POST':
        user_id = get_user_id()
        task_id = request.form['taskid']
        text = request.form.get('commenttext')
        new_comment = Comment(user_id=user_id, task_id=task_id, timestamp=datetime.now(), text=text)
        app.logger.info('### Post Comment to db ###\n' +
                        'For user: ' + str(user_id) + ' and Task ID: ' + task_id + '\n' +
                        'With text: ' + text + '\n' +
                        'Resulted request: ' + str(new_comment))  # debug
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('task', action='view', id=int(request.form['taskid'])))


@app.route("/edit_comment_to_task", methods=['POST'])
def edit_comment_to_task():
    user_id = get_user_id()
    if user_id is None:
        return redirect(url_for('do_login'))

    # ['commenttext', 'oldcommenttext', 'taskid', 'commentid']
    # app.logger.info(request.form.keys())
    task_id = request.form.get('taskid')
    comment_id = request.form.get('commentid')
    comment_text = request.form.get('commenttext')
    if can_user_edit_in_this_task_comment(user_id, task_id, comment_id):
        # db.session.query().\
        #     filter(Comment.id == comment_id).\
        #     update({"text": comment_text})
        Comment.query.filter_by(id = comment_id).update({"text": comment_text})
        db.session.commit()
        return 'Ok'

    return 'Not Ok' # redirect(url_for('task', action='view', id=int(request.args.get('tid'))))


###########################
######### PROJECT #########
###########################
@app.route("/project")
@app.route("/project/<action>", methods=['GET', 'POST'])
def project(action='list'):
    try:
        user_id = get_user_id()
        app.logger.info(' ### Project | logined user ID:\t' + str(user_id))  # debug
        if user_id is None:
            return redirect(url_for('do_login'))  # if not logined go to login
    except:
        app.logger.error('Not logined')  # debug
        return redirect(url_for('do_login'))  # if not logined go to login

    ### Show Project List ###
    if action == 'list' or action == 'list_closed':
        if action == 'list_closed':
            project_status = False
            project_ids = get_projects_for_user(user_id, 'Disabled')
        else:
            project_status = True
            project_ids = get_projects_for_user(user_id, 'Active')

        # app.logger.debug('project_ids: '+str(project_ids)) # debug
        projects = []
        project_users = []
        if project_ids:
            for project_id in project_ids:
                project_name = db.session.query(Project.name).filter_by(id=project_id[0]).all()[0]
                projects.append([project_id[0], project_name[0]])
                project_user_ids = db.session.query(ProjectAssociation.user_id).filter_by(
                    project_id=project_id[0]).all()
                project_user_names = []
                for user_id in project_user_ids:
                    name = db.session.query(User.nickname).filter_by(id=user_id[0]).one_or_none()
                    if name:
                        project_user_names.append(name[0])
                project_users.append(project_user_names)

                # app.logger.debug('project_users is: '+str(project_user_names)) # debug
        return render_template('project/list.html', title=u'Проекты', user=get_nick(), project_list=projects,
                               project_status=project_status, project_users=project_users)

    ### Create new Project ###
    elif action == 'create':
        user_id = get_user_id()
        if request.method == 'POST':
            # Need:
            #       User ID (upper)
            #       Project Name
            #       Project ID
            project_name = request.form.get('projectname')

            db.session.add(Project(name=project_name, status='Active', owner=user_id))
            db.session.commit()
            project_id = db.session.query(Project.id).filter_by(name=project_name)
            db.session.add(ProjectAssociation(user_id=user_id, project_id=project_id[0][0]))
            db.session.commit()
            return redirect(url_for('project'))  # got to project list

        else:  # if GET request
            return render_template('project/create.html', title=u'Проекты', user=get_nick(), user_id=user_id)

    ### View Project ###
    elif action == 'view':
        project_id = str(request.args.get('id'))
        app.logger.debug('### Setting cookie ###\nProject ID for view: ' + str(project_id))  # debug
        response = app.make_response(redirect(url_for('task', action='list', project_id=project_id)))
        response.set_cookie('project_id', value=project_id)
        return response  # go to task list with cookie 'project_id' set

    ### Edit Project ###
    elif action == 'edit':
        project_id = request.args.get('id')
        if request.method == 'POST':
            project_name = request.form.get('projectname')
            need_add_user = request.form.getlist('addusertoggle')
            if need_add_user:
                user_to_add = request.form.get('adduser')
                try:
                    userid_to_add = db.session.query(User.id).filter_by(nickname=user_to_add).first()[0]
                    db.session.add(ProjectAssociation(user_id=userid_to_add, project_id=project_id))
                    db.session.commit()
                    app.logger.info('User existed')
                    app.logger.info('Checkbox is: Checked\n' + str(user_to_add) + '\n' + str(userid_to_add))
                except:
                    app.logger.info('User doesn\'t exist')
                    return "Error: User doesn't exist"

            else:
                app.logger.info('Checkbox is: Unchecked\n Not need to add user\n' + str(need_add_user))

            db.session.query(Project).filter_by(id=project_id).update({
                'name': project_name,
                'status': 'Active',
                'owner': user_id})
            db.session.commit()
            return redirect(url_for('project', action='list', project_id=project_id))
        else:  # if GET request
            # Need:
            #       Project ID
            #       Project Name
            #       Project Users
            project_name = db.session.query(Project.name).filter_by(id=project_id).all()[0]
            project_user_ids = db.session.query(ProjectAssociation.user_id).filter_by(project_id=project_id)

            project_user_names = []
            user_ids = []
            for user_id in project_user_ids:
                name = db.session.query(User.nickname).filter_by(id=user_id[0]).one_or_none()
                if name:
                    project_user_names.append(name[0])
                user_ids.append(user_id[0])

            project_user_ids = user_ids
            # app.logger.debug('### Project # Edit ### id from form: '+str(project_id[0])+'\n'+ \
            #                   'Name: '+str(project_name[0])+'\n'+ \
            #                   'User IDs: '+str(project_user_ids)+'\n'+ \
            #                   'Users in project: '+str(project_user_names) ) # debug
            project_full_data = [project_id, project_name[0], project_user_ids, project_user_names]
            response = app.make_response(
                render_template('project/edit.html', title=u'Проекты', user=get_nick(), project=project_full_data))
            response.set_cookie('project_id', value=project_id)
            return response  # go to project editor with cookie 'project_id' set

    ### Remove user from Project ###
    elif action == 'rmuser':
        project_id = str(request.cookies.get('project_id'))
        userid_to_del = str(request.args.get('id'))
        cur = db.session.query(ProjectAssociation).filter_by(user_id=userid_to_del).filter_by(
            project_id=project_id).delete()
        db.session.commit()
        app.logger.debug(
            "### Trying to delete user: " + str(userid_to_del) + "\nFrom project: " + project_id + "\n" + str(cur))
        return redirect(url_for('project', action='edit', id=project_id))


###########################
#### Another locations ####
###########################

@app.route("/profile")
def profile():
    if not logined_by_cookie():
        return redirect(url_for('do_login'))  # if not logined go to login
    else:
        username = get_nick()
        user_id = request.cookies.get('id')
        email = db.session.query(User.email).filter_by(id=user_id).one()[0]
        return render_template('profile.html', user=username, mail=email, user_id=user_id)


@app.route("/profile/edit", methods=['GET', 'POST'])
def profile_edit():
    if not logined_by_cookie():
        return redirect(url_for('do_login'))  # if not logined go to login
    else:
        user_id = request.cookies.get('id')
        username = str(get_nick()) + ' ' + str(user_id)
        email = db.session.query(User.email).filter_by(id=user_id).one()[0]
        if request.method == 'GET':
            return render_template('profile_edit.html', user=username, mail=email)
        elif request.method == 'POST':
            original_password = request.form.get('orig_pass')
            from crypt import crypt
            salt = '$6$FIXEDS'
            pass_hash = crypt(original_password, salt)
            hash_from_db = db.session.query(User.p_hash).filter_by(id=user_id).one()[0]
            app.logger.debug('Passwords:\n' + str(pass_hash) + '\n' + str(hash_from_db))  # debug
            if pass_hash == hash_from_db:
                mail = request.form.get('email')
                new_password = request.form.get('new_pass')
                if new_password is None:
                    db.session.query(User).filter_by(id=user_id).update({'email': mail})
                    db.session.commit()
                else:  # update pass
                    salt = '$6$FIXEDS'
                    pass_hash = crypt(new_password, salt)
                    db.session.query(User).filter_by(id=user_id).update({
                        'email': mail,
                        'p_hash': pass_hash,
                        'password': original_password})
                    db.session.commit()
                    app.logger.debug('SETTING Password:\n' + str(pass_hash))  # debug
            else:
                return "wrong password"

            return render_template('profile.html', user=username, mail=email)


@app.route("/about")
def about():
    return render_template('about.html', title=u'О сайте')


@app.route("/login", methods=['GET', 'POST'])
def do_login():
    if request.method == 'POST':
        try:
            user = str(request.form['username'])
            password = str(request.form['password'])
        except UnicodeEncodeError:
            return "Wrong login or password charset"

        # app.logger.info('Check password:\t'+str(check_passwd(user, password))) # debug
        if check_passwd(user, password):
            # Set Cookies for knowing about user on other pages
            auth_hash = str(id_generator())
            user_id = int(get_user_id_from_db(user))
            app.logger.debug('Set cookies ' + str(user) + ' ' + str(user_id) + ' ' + auth_hash)  # debug

            response = app.make_response(redirect(url_for('index')))
            response.set_cookie('id', value=str(user_id))
            response.set_cookie('hash', value=auth_hash)
            response.set_cookie('logged_at', value=str(datetime.now()))
            db.session.query(User).filter_by(id=user_id).update({'cookie': auth_hash})
            db.session.commit()
            # sql = "UPDATE user SET cookie='{}' WHERE id='{}'".format(auth_hash, user_id)
            # app.logger.info('SQL:\t'+str(sql)) # debug
            # db.session.execute(sql)
            return response  # need for set cookies finaly
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
            import crypt
            salt = '$6$FIXEDS'
            pass_hash = crypt.crypt(request.form.get('password'), salt)
            user_row = User(nickname=request.form.get('username'),
                            email=request.form.get('email'),
                            password=request.form.get('password'),
                            p_hash=pass_hash,
                            role=ROLE_USER,
                            register_date=datetime.now())
            app.logger.info('Registered user:\n' +
                            request.form.get('username') + '\n' +
                            request.form.get('email') + '\n' +
                            pass_hash + '\n')  # debug
            db.session.add(user_row)
            try:
                db.session.commit()
            except IntegrityError:
                return "Try another e-mail."

            # Getting id of new user for project owner
            user_id = db.session.query(User.id).filter_by(email=request.form.get('email')).all()[0][0]
            app.logger.info('NEW USER ID:\t' + str(user_id))  # debug
            # Prepare empty project for user
            new_project = Project(name=u'Добро пожаловать',
                                  status='Active',
                                  owner=user_id)
            db.session.add(new_project)
            db.session.commit()

            # Getting Greet project id for assign task
            new_project_id = db.session.query(Project.id).filter_by(name=u'Добро пожаловать', owner=user_id).all()[0][0]
            # Creating user association to project
            new_assoc = ProjectAssociation(user_id=user_id, project_id=new_project_id)
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
        return redirect(url_for('do_login'))  # if not logined go to login
    else:
        user_id = get_user_id()

    cur = db.session.execute("select id,nickname,email from user")
    user_list = cur.fetchall()
    return render_template('user_list.html', user=get_nick(), user_list=user_list)


#############################################
### Functions ###
#################
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
        app.logger.info('### Email exist in database ###')  # debug
        return True
    else:
        app.logger.info('### Email doesn\'t exist in database ###')  # debug
        return False


def get_user_id_from_db(username):
    cur = db.session.execute("SELECT id FROM user WHERE nickname='{0}'".format(str(username)))
    return cur.fetchone()[0]


def check_passwd(login, password):
    try:
        db_hash = get_hash_from_db(login)[0]
    except TypeError:
        return 0
    if db_hash:  # exist
        salt_end = db_hash.rindex('$')
        salt = db_hash[:salt_end]
        import crypt
        crypted_pass_hash = crypt.crypt(password, salt)
        if crypted_pass_hash == db_hash:
            return 1  # Passwords equal
        else:
            return 0  # Not equal
    else:
        return 0  # p_hash doesn't exist


def logined_by_cookie():
    user_id = str(request.cookies.get('id'))
    user_hash = request.cookies.get('hash')
    if user_hash:
        app.logger.info('Check UserID from cookie:\t' + user_id + ' ' + user_hash)  # debug

        if not user_id == str('None'):  # if user_id exist
            cur = db.session.execute("SELECT cookie FROM user WHERE id='{0}'".format(user_id))
            cookie = cur.fetchone()[0]  # getting hash
            # app.logger.debug('Cookie from db:\t\t'+str(cookie)) # debug

            if str(cookie) == str(user_hash):
                return True  # yeah LOGINED

    return False


def get_nick():
    user_id = request.cookies.get('id')
    if user_id:
        cur = db.session.execute("SELECT nickname FROM user WHERE id='{0}'".format(int(user_id)))
        return cur.fetchone()[0]

    return None


def convert_id_to_nick(comments):
    result = list()
    app.logger.debug("### START Convert IDs to Nicks ###\nSource data:\n" + str(comments))  # debug
    for comment in comments:
        nick = User.query.filter_by(id=comment[1]).first().nickname
        converted_comment = (comment[0], comment[1], comment[2], comment[3], nick)
        app.logger.debug("### Convert IDs to Nicks ###\n" + str(converted_comment) + "\n" + str(comment))  # debug
        result.append(converted_comment)

    app.logger.debug("Converted result: " + str(result))
    return result


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
        project_ids = db.session.query(ProjectAssociation.project_id).filter_by(user_id=user_id).all()

    return project_ids


def get_first_project_id(user_id):
    p = get_projects_for_user(user_id)[0][0]
    app.logger.debug("First Project ID for this user: " + str(p))
    return p


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    import random
    return ''.join(random.choice(chars) for _ in range(size))


def quick_sort(lst, parent_id, sorteded):
    sorted_list = sorteded
    for eid, taskname, date, parent, depth in lst:
        if parent == parent_id:
            element = {'id': eid, 'name': taskname, 'date': date, 'parent': parent, 'depth': depth}
            sorted_list.append(element)
            t = quick_sort(lst, eid, sorted_list)

    return sorted_list

    tasks = tasks_short_date
    # for task in tasks:
    #   app.logger.debug('Task preview:\t'+str(task)) # debug
    return tasks


def order_tasks(tasks, parent_id, partially_sorted):
    sorted_tasks = partially_sorted
    for task in tasks:
        if task.parent_id == parent_id:
            sorted_tasks.append(task)
            order_tasks(tasks, task.id, sorted_tasks)

    return sorted_tasks


def get_comment_author_id(comment_id):
    # user_id = db.session.query(Comment.user_id).filter_by(id=comment_id).one_or_none()
    user_id = db.session.query(Comment.user_id).filter_by(id=comment_id).one_or_none()[0]
    print("RAW comment user ID: %s FOR COMMENT ID: %s" % (user_id, comment_id))
    return user_id


def can_user_edit_in_this_task_comment(user_id, task_id, comment_id):
    # Check access to task
    if permit_to_project(user_id, task_id):
        # Check owner of comment
        comment_owner = db.session.query(Comment.user_id).filter_by(id=comment_id).one_or_none()[0]
        # app.logger.info(comment_owner)
        if user_id == comment_owner:
            return True
        else:
            return False


def permit_to_project(user_id, task_id):
    # check access to current project
    project_id = db.session.execute("SELECT project_id FROM task WHERE id='{}'".format(task_id)).fetchone()[0]
    permit_to_project = db.session.execute(
        "SELECT id FROM project_association WHERE project_id='{}' AND user_id='{}'".format(project_id,
                                                                                           user_id)).fetchone()[0]
    if permit_to_project: return True
    else: return False



####################################
######### TEMPLATE FILTERS #########
####################################
@app.template_filter('format_timestamp')
def format_timestamp(timestamp):
    return str(timestamp).split(".")[0]
