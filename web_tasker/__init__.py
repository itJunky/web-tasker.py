# -*- coding: utf-8 -*-

from flask import Flask
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy

def create_app(config_filename):
  # for static files
  app = Flask(__name__, instance_relative_config=True, instance_path='/code')
  app.config.from_pyfile(os.path.join(app.instance_path, config_filename))
  app.config['STATIC_URL_PATH'] = 'static'
  #app.config['DEBUG'] = True

  bootstrap = Bootstrap()
  bootstrap.init_app(app)

  # show startup flask variables
  from pprint import pprint
  items = app.config.viewitems()
  for i in items: pass
      # print(i)

  return app

import os
app = create_app('config_db.py')

## prepare database
from web_tasker.models import db
db.init_app(app)

# run url handler after all prepare code
import web_tasker.views
