#!/bin/bash

pip install --upgrade pip
pip install -r requirements.txt

# Backup and migrate db
# DATE=`date +%Y-%m-%d__%H_%M_%S`; cp app.db ./backup_db/app_${DATE}.db; python ./db_migrate.py

# Run application server
python ./runserver.py

# python ./db_create.py
#python ./show_python_modules.py

# Get back old schema
# python ./db_downgrade.py
