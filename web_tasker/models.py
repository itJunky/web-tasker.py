# from web_tasker import db
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

ROLE_USER = 0
ROLE_ADMIN = 1


class ProjectAssociation(db.Model):
    __tablename__ = 'project_association'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    project_id = db.Column(db.Integer, index=True)

    def __repr__(self):
        return '<Project association between user_id %r and project_id %r>' % (self.user_id, self.project_id)


class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    status = db.Column(db.String(10))
    owner = db.Column(db.Integer)  # user.id

    def __repr__(self):
        return '<Project %r have users %r>' % (self.name, self.users)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    p_hash = db.Column(db.String(96))
    password = db.Column(db.String(24))
    cookie = db.Column(db.String(8))
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    register_date = db.Column(db.DateTime)

    def __repr__(self):
        return '<User %r>' % self.nickname


class Task(db.Model):
    __tablename__ = 'task'

    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, default=0, index=True)
    body = db.Column(db.String())
    taskname = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, index=True)
    status = db.Column(db.String(10))
    depth = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Task %r>' % self.body


class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    task_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    text = db.Column(db.String())

    def __repr__(self):
        return '<Comment %r>' % self.text
