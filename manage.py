'''Management commands.'''

import os
from flask.ext.script import Manager
from managrr import app, db, models
from flask.ext.migrate import Migrate, MigrateCommand

manager = Manager(app)
app.config.from_object('config.BaseConfiguration')

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def install():
    '''Installs all required packages.'''
    os.system('pip install -U -r requirements.txt')


@manager.shell
def make_shell_context():
    return dict(app=app, db=db, models=models)


if __name__ == "__main__":
    manager.run()
