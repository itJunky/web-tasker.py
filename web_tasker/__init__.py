# -*- coding: utf-8 -*-

from flask import Flask
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy

def create_app(config_filename):
  # for static files
  app = Flask(__name__, static_url_path='/static/', instance_relative_config=True)
  app.config.from_pyfile(config_filename)
  app.config['STATIC_URL_PATH'] = 'static'
  app.config['DEBUG'] = True

  bootstrap = Bootstrap()
  bootstrap.init_app(app)

  ## set the secret key.  keep this really secret:
  #app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

  from pprint import pprint
  items = app.config.viewitems()
  for i in items:
      print(i)

  return app

import os
app = create_app(os.path.join('/www/tasker.itjunky.ws/web-tasker.py','config_db.py'))

## prepare database
from web_tasker.models import db
db.init_app(app)

# run url handler after all prepare code
import web_tasker.views
