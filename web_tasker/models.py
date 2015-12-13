from web_tasker import db
import datetime

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(64), index = True, unique = True)
    p_hash = db.Column(db.String(96))
    password = db.Column(db.String(24))
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    register_date = db.Column(db.DateTime)
    posts = db.relationship('Task', backref = 'author', lazy = 'dynamic')

    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String())
    # need more but not work
    taskname = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(10))

    def __repr__(self):
        return '<Task %r>' % (self.body)
