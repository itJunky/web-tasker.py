#from web_tasker import db
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

ROLE_USER = 0
ROLE_ADMIN = 1
#SELECT pa.project_id,u.nickname FROM project_association pa, user u WHERE pa.user_id='{}' and u.user_id='{}'
class Project_association(db.Model):
    __tablename__   = 'project_association'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    project_id = Column(Integer, index=True)

    def __repr__(self):
        return '<Project association between user_id %r and project_id %r>' % (self.user_id, self.project_id)

class Project(db.Model):
    __tablename__   = 'project'

    id              = Column(Integer, primary_key=True)
    name            = Column(String(255))
    #owner           = Column(Integer) #user.id

    def __repr__(self):
        return '<Project %r have users %r>' % (self.name, self.users)

db = SQLAlchemy()

class User(db.Model):
    __tablename__   ='user'

    id              = Column(Integer, primary_key = True)
    nickname        = Column(String(64), index = True, unique = True)
    email           = Column(String(64), index = True, unique = True)
    p_hash          = Column(String(96))
    password        = Column(String(24))
    cookie          = Column(String(8))
    role            = Column(db.SmallInteger, default = ROLE_USER)
    register_date   = Column(db.DateTime)

    def __repr__(self):
        return '<User %r>' % (self.nickname)
    
class Task(db.Model):
    __tablename__   ='task'

    id              = Column(Integer, primary_key = True)
    body            = Column(String())
    taskname        = Column(String(140))
    timestamp       = Column(db.DateTime)
    user_id         = Column(Integer, ForeignKey('user.id'))
    project_id      = Column(Integer, ForeignKey('project.id'))
    status          = Column(String(10))

    def __repr__(self):
        return '<Task %r>' % (self.body)

class Comment(db.Model):
    __tablename__   ='comment'

    id              = Column(Integer, primary_key = True)
    user_id         = Column(Integer)
    task_id         = Column(Integer)
    timestamp       = Column(db.DateTime)
    text            = Column(String())

    def __repr__(self):
        return '<Comment %r>' % (self.text)
