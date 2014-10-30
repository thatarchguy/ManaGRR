from flask import render_template, request
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

@app.route('/client/<int:client_id>/admin')
def client_admin(client_id):
    client = models.Clients.query.get(client_id)
    nodes  = client.nodes.all()
    return render_template('clientadmin.html', title=client.name, client=client, nodes=nodes)


@app.route('/client/<int:client_id>/edit', methods=['POST'])
def client_edit(client_id):
    attribute = request.form['id']
    value = request.form['value']

    if attribute == "clientName":
        client = models.Clients.query.get(client_id)
        client.name = value
        db.session.commit()

    elif attribute == "clientDate":
        client = models.Clients.query.get(client_id)
        client.date = value
        db.session.commit()

    elif attribute == "clientEmail":
        client = models.Clients.query.get(client_id)
        client.email = value
        db.session.commit()
    
    elif attribute == "clientPhone":
        client = models.Clients.query.get(client_id)
        client.phone = value
        db.session.commit()

    else:
        value = "error"

    return value


@app.route('/settings')
def settings_view():
    return render_template('settings.html', title="Settings")
