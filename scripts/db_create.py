#!/usr/bin/env python

from migrate.versioning import api
from managrr import app, db
import os.path
import config

db.create_all()

app.config.from_object('config.BaseConfiguration')

SQLALCHEMY_MIGRATE_REPO = app.config['SQLALCHEMY_MIGRATE_REPO']
SQLALCHEMY_DATABASE_URI = app.config['SQLALCHEMY_DATABASE_URI']

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))
