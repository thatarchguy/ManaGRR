from flask import render_template
from app import app,db,models
import datetime

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index_view():

    # SQLAlchemy to get total clients
    clientCount = models.Clients.query.count()
    nodeCount   = models.Nodes.query.count()

    return render_template('index.html',
                            title="Dashboard", 
                            clientCount=clientCount, 
                            nodeCount=nodeCount)


@app.route('/login')
def login_view():
    return render_template('login.html')


@app.route('/clients')
def clients_view():

    # SQLAlchemy functions here
    clients = models.Clients.query.all()
    
    return render_template('clients.html', title="Clients", entries=clients)


@app.route('/settings')
def settings_view():
    return render_template('settings.html', title="Settings")
