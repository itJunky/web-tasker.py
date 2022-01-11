from migrate.versioning import api
from config_db import SQLALCHEMY_DATABASE_URI
from config_db import SQLALCHEMY_MIGRATE_REPO
from web_tasker import app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


import os.path

with app.app_context():
        # Extensions like Flask-SQLAlchemy now know what the "current" app
        # is while within this block. Therefore, you can now run........
        db.create_all()
# db.create_all()
#db.create_all(app)
#db.create_all()

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
