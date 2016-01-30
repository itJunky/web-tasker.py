from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
comments = Table('comments', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('user_id', INTEGER),
    Column('task_id', INTEGER),
    Column('timestamp', DATETIME),
    Column('text', VARCHAR),
)

comment = Table('comment', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer),
    Column('task_id', Integer),
    Column('timestamp', DateTime),
    Column('text', String),
)

project = Table('project', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=255)),
)

task = Table('task', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('taskname', String(length=140)),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
    Column('project_id', Integer),
    Column('status', String(length=10)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['comments'].drop()
    post_meta.tables['comment'].create()
    post_meta.tables['project'].create()
    post_meta.tables['task'].columns['project_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['comments'].create()
    post_meta.tables['comment'].drop()
    post_meta.tables['project'].drop()
    post_meta.tables['task'].columns['project_id'].drop()
