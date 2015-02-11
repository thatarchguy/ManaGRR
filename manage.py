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


@manager.command
def test():
    '''Runs the tests.'''
    command = 'nosetests --verbosity=2 --nocapture'
    os.system(command)


@manager.command
def lint():
    '''Lints the codebase'''
    command = 'flake8 --ignore E127,E221,F401 --max-line-length=220 --exclude=db_repository,tests,env,migrations .'
    os.system(command)


@manager.command
def clean():
    '''Cleans the codebase'''
    commands = ["find . -name '*.pyc' -exec rm -f {} \;", "find . -name '*.pyo' -exec rm -f {} \;", 
                "find . -name '*~' -exec rm -f {} \;", "find . -name '__pycache__' -exec rmdir {} \;", 
                "rm -f app.db", "rm -rf migrations", "rm -f managrr.log"]
    for command in commands:
        print "Running " + command
        os.system(command)


if __name__ == "__main__":
    manager.run()