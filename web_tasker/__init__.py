# -*- coding: utf-8 -*-

#from flask import Flask, render_template, request, send_from_directory, request, session, redirect, url_for
from flask import Flask
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy


sessions = {'username': 'tester'}
user = None
# for static files
def create_app():
  app = Flask(__name__, static_url_path='/static/')
  Bootstrap(app)
  return app

app = create_app()
# prepare database
app.config.from_object('config_db')
db = SQLAlchemy(app)
from web_tasker import views, models

import web_tasker.views

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
