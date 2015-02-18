from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.login import LoginManager
from flask.ext.bcrypt import Bcrypt
from rq import Queue
from rq.job import Job
from worker import conn
from rq_dashboard import RQDashboard

app = Flask(__name__)
app.config.from_object('config.BaseConfiguration')
db = SQLAlchemy(app)
toolbar = DebugToolbarExtension(app)

login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt()
q = Queue(connection=conn)
RQDashboard(app)

import logging
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler('managrr.log', 'a',
                                   1 * 1024 * 1024, 10)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('managrr startup')


from managrr import views, models
