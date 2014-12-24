from flask import render_template, request, flash, redirect, url_for
from managrr import app, db, models
from .forms import CreateNode, AddClient
import os
import datetime
import subprocess
import re


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


@app.route('/client/<int:client_id>/admin/')
def client_admin(client_id, new_client=False):
    new_client = request.args.get('new_client')
    client  = models.Clients.query.get(client_id)
    nodes   = client.nodes.all()
    digikey = models.Keys.query.filter_by(client_id=client_id).one().digiocean
    awskey  = models.Keys.query.filter_by(client_id=client_id).one().aws

    CreateNodeForm = CreateNode(digiocean=digikey, aws=awskey)
    app.logger.info(digikey)
    if (new_client == None):  # noqa
        new_client = check_status(client.id)

    return render_template('clientadmin.html',
                            title=client.name,
                            client=client,
                            nodes=nodes,
                            CreateNodeForm=CreateNodeForm,
                            new_client=new_client)


@app.route('/client/<int:client_id>/admin/edit', methods=['POST'])
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


@app.route('/clients/add', methods=['POST', 'GET'])
def client_add():

    AddClientForm = AddClient()
    if AddClientForm.validate_on_submit():

        # Add duplicate checking

        newClient = models.Clients(name=AddClientForm.name.data, date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    phone=AddClientForm.phone.data, email=AddClientForm.email.data, size=AddClientForm.size.data)
        clientKeys = models.Keys(aws=AddClientForm.aws.data, digiocean=AddClientForm.digitalOcean.data, ssh=AddClientForm.ssh.data, client_id=newClient.id)
        db.session.add(newClient)
        db.session.add(clientKeys)
        db.session.commit()

        client = models.Clients.query.get(newClient.id)

        build_client_local(client, "all")

        return redirect(url_for('client_admin', client_id=newClient.id, new_client=True))

    return render_template('addclient.html', title='Add Client', AddClientForm=AddClientForm)


@app.route('/api/nodes/create/', methods=['POST', 'GET'])
def node_create(client=None, role=None, location=None):
    if request.method == 'POST':
        clientName  = request.form['client']
        role        = request.form['roles']
        location    = request.form['location']
        key         = request.form['key']
    # This function was tested in python CLI. Seems to work.
        clientID = models.Clients.query.filter_by(name=clientName).one().id
    elif client is not None:
        clientID  = client.id
        role        = role
        location    = location
        if location == "aws":
            key  = models.Keys.query.get(client_id).aws
        elif location == "digiocean":
            key = models.Keys.query.get(client_id).digiocean
 
        
    else:
        return "0"
   
    """
    clientKey = models.Keys(aws=AddClientForm.aws.data, digiocean=AddClientForm.digitalOcean.data, ssh=AddClientForm.ssh.data, client_id=clientID)
    db.session.add(clientKey)
    db.session.add(clientKey)
    db.session.commit()
    """

    return "1"


@app.route('/api/nodes/checkin/', methods=['GET'])
def node_checkin():
    clientName  = request.args.get('client')
    role        = request.args.get('role')
    ip          = request.args.get('ip')

    # This function was tested in python CLI. Seems to work.
    clientID = models.Clients.query.filter_by(name=clientName).one().id

    # We only want the first one, right? Yeah? Ideally hm... This could mess up if cloud workers provision faster than proxmox workers.
    node = models.Nodes.query.filter_by(client_id=clientID, type=role, IP='0.0.0.0').one()
    node.IP = ip
    db.session.commit()
    app.logger.info(clientName + " " + role + " " + ip + " Checked in")

    # Some nonexistent error checking straight to ok
    status = "1"

    return status


@app.route('/client/<int:client_id>/status')
def client_status(client_id):
    if (os.path.isfile("managrr/provision/" + str(client_id) + ".lockfile")):
        with open("managrr/provision/" + str(client_id) + ".lockfile", 'r') as f:
            status = f.readline()
            f.close()
        if str(status.rstrip()) == "sysprep":
            percent = "30"
        elif str(status.rstrip()) == "proxmox":
            percent = "50"
        elif str(status.rstrip()) == "installing":
            percent = "80"
        else:
            percent = "10"
        return percent
    return "0"


@app.route('/api/nodes/history')
def node_history():
    # I need to finish the 'add worker' problem before I work on this
    # Query database count all for latest
    jsondumps = "boilerplate"

    return jsondumps


@app.route('/settings')
def settings_view():
    return render_template('settings.html', title="Settings")


def check_status(client_id):
    if (os.path.isfile("managrr/provision/" + str(client_id) + ".lockfile")):
        return True

    return False


def build_client_local(client, role):
    lastVid = models.Nodes.query.order_by(models.Nodes.vid.desc()).first()
    if lastVid is None:
        vid = 200
    else:
        vid = lastVid.vid + 1
    if (role == "all"):
        lastInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).first()
        if lastInterface is None:
            inter = "vmbr10"
        else:
            inter = str(lastInterface.net)
            interid = re.split('(\d+)', inter)
            inter = "vmbr" + str(int(interid[1]) + 1)
    elif (role == "worker"):
        # Probably going to need to expand more here when EC2 and DigiOcean come into play
        clientInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).filter(models.Nodes.client_id == client.id).first()
        inter = str(clientInterface.net)
    if check_status(client.id) is True:
        return False
    app.logger.info("Building: " + role + " for newclient " + client.name)
    arguments = "-c " + client.name + " -b " + str(client.id) + " -v " + str(vid) + " -r " + role + " -n seanconnery" + " -i " + inter
    subprocess.Popen(["bash wrapper.sh " + arguments], shell=True, executable="/bin/bash", cwd=os.getcwd() + "/managrr/provision/")
    # Due to the nature of the database model, we need to insert basic information about nodes here.
    # They will be updated with ip address upon creation
    if (role == "all"):
        addWorker   = models.Nodes(client_id=client.id, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
        addDatabase = models.Nodes(client_id=client.id, type="database", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
        addControl  = models.Nodes(client_id=client.id, type="control", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
        db.session.add(addWorker)
        db.session.add(addDatabase)
        db.session.add(addControl)
        db.session.commit()
    elif (role == "worker"):
        addWorker = models.Nodes(client_id=client.id, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
        db.session.add(addWorker)
        db.session.commit()
    return True
