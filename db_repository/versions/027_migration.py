from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
project = Table('project', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=255)),
    Column('status', String(length=10)),
    Column('owner', Integer),
)

task = Table('task', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('parent_id', Integer),
    Column('body', String),
    Column('taskname', String(length=140)),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
    Column('project_id', Integer),
    Column('status', String(length=10)),
    Column('depth', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['project'].columns['owner'].create()
    post_meta.tables['project'].columns['status'].create()
    post_meta.tables['task'].columns['depth'].create()
    post_meta.tables['task'].columns['parent_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['project'].columns['owner'].drop()
    post_meta.tables['project'].columns['status'].drop()
    post_meta.tables['task'].columns['depth'].drop()
    post_meta.tables['task'].columns['parent_id'].drop()
