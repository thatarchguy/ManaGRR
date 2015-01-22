from flask import render_template, request, flash, redirect, url_for
from managrr import app, db, models
from .forms import CreateNode, AddClient, AddHyper
from dateutil.relativedelta import relativedelta
import os
import datetime
import time
import subprocess
import re
import json


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
    clientCount = models.Clients.query.filter_by(active=True).count()
    hyperCount   = models.Hypervisors.query.count()

    return render_template('index.html',
                            title="Dashboard",
                            clientCount=clientCount,
                            hyperCount=hyperCount)


@app.route('/login')
def login_view():
    return render_template('login.html')


@app.route('/hypervisors')
def hypervisors_view():

    # SQLAlchemy functions here
    hypervisors = models.Hypervisors.query.all()

    return render_template('hypervisors.html', title="Hypervisors", entries=hypervisors)


@app.route('/hypervisors/add', methods=['POST', 'GET'])
def hypervisor_add():
    error = None
    AddHyperForm = AddHyper()
    if AddHyperForm.validate_on_submit():
        if models.Hypervisors.query.filter_by(IP=AddHyperForm.ip.data).first() is None:
            newHypervisor = models.Hypervisors(location=AddHyperForm.location.data, IP=AddHyperForm.ip.data)
            db.session.add(newHypervisor)
            db.session.commit()

            return redirect('/hypervisors')
        else:
            error = "Client IP is already in use"

    return render_template('addhyper.html', title="Add Hypervisor", AddHyperForm=AddHyperForm, error=error)


@app.route('/clients')
def clients_view():

    # SQLAlchemy functions here
    clients = models.Clients.query.filter_by(active=True).all()

    return render_template('clients.html', title="Clients", entries=clients)


@app.route('/client/<int:client_id>/admin/')
def client_admin(client_id, new_client=False):
    new_client = request.args.get('new_client')
    new_worker = request.args.get('new_worker')
    client  = models.Clients.query.get(client_id)
    nodes   = client.nodes.filter_by(active=True).all()
    digikey = models.Keys.query.filter_by(client_id=client_id).first().digiocean
    awskey  = models.Keys.query.filter_by(client_id=client_id).first().aws
    hypervisorIP    = models.Hypervisors.query.get(client.hyperv_id).IP
    CreateNodeForm  = CreateNode(digiocean=digikey, aws=awskey)
    if (new_client == None):  # noqa
        new_client = check_status(client.id)
    if (new_worker == None):  # noqa
        new_worker = check_status(client.id, "worker")
    return render_template('clientadmin.html',
                            title=client.name,
                            client=client,
                            nodes=nodes,
                            CreateNodeForm=CreateNodeForm,
                            new_client=new_client,
                            new_worker=new_worker,
                            hypervisorIP=hypervisorIP)


@app.route('/client/<int:client_id>/delete/')
def client_delete(client_id):
    client  = models.Clients.query.get(client_id)
    nodes   = models.Nodes.query.filter_by(client_id=client.id)
    keys    = models.Keys.query.filter_by(client_id=client.id).first()

    if client.active is False:
        return redirect(url_for('index.view'))

    for node in nodes:
        node.active = False
        node.date_rm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.session.add(node)
    client.active = False
    client.date_rm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.session.add(client)
    db.session.delete(keys)
    db.session.commit()

    return redirect(url_for('index_view'))


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
    error = None
    AddClientForm = AddClient()
    AddClientForm.hyperv.choices = [(a.IP, a.IP) for a in models.Hypervisors.query.order_by('IP')]
    if AddClientForm.validate_on_submit():
        if models.Clients.query.filter_by(name=AddClientForm.name.data).first() is None:
            newClient = models.Clients(name=AddClientForm.name.data, date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        phone=AddClientForm.phone.data, email=AddClientForm.email.data, size=AddClientForm.size.data)

            hypervisor = models.Hypervisors.query.filter_by(IP=AddClientForm.hyperv.data).first()
            newClient.hyperv_id = hypervisor.id
            db.session.add(newClient)

            db.session.commit()
            clientKeys = models.Keys(aws=AddClientForm.aws.data, digiocean=AddClientForm.digitalOcean.data, ssh=AddClientForm.ssh.data, client_id=newClient.id)
            db.session.add(clientKeys)
            db.session.commit()

            if AddClientForm.aws.data != "":
                app.logger.info("ClientKey Added: [NEWCLIENT]" + str(newClient.id) + "," + newClient.name + ",aws")
            if AddClientForm.digitalOcean.data != "":
                app.logger.info("ClientKey Added: [NEWCLIENT]" + str(newClient.id) + "," + newClient.name + ",digiocean")
            if AddClientForm.ssh.data != "":
                app.logger.info("ClientKey Added: [NEWCLIENT]" + str(newClient.id) + "," + newClient.name + ",ssh")

            client = models.Clients.query.get(newClient.id)

            build_client_local(client, "all")

            return redirect(url_for('client_admin', client_id=newClient.id, new_client=True))
        else:
            error = "Client Name is already in use"

    return render_template('addclient.html', title='Add Client', AddClientForm=AddClientForm, error=error)


@app.route('/api/nodes/create/', methods=['POST', 'GET'])
def node_create(client=None, role=None, location=None):
    if request.method == 'POST':
        clientName  = request.form['client']
        location    = request.form['location']
        digiocean   = request.form['digiocean']
        aws         = request.form['aws']
    # This function was tested in python CLI. Seems to work.
        client = models.Clients.query.filter_by(name=clientName).first()
        if location == "aws":
            key = aws
            clientKey = models.Keys.query.filter_by(client_id=client.id).first()
            clientKey.aws = key
            app.logger.info("ClientKey Added: " + str(client.id) + "," + client.name + "," + location)
            db.session.commit()
            build_client_aws(client, key)
        elif location == "digiocean":
            key = digiocean
            clientKey = models.Keys.query.filter_by(client_id=client.id).first()
            clientKey.digiocean = key
            app.logger.info("ClientKey Added: " + str(client.id) + "," + client.name + "," + location)
            db.session.commit()
            build_client_digiocean(client, key)
        elif location == "proxmox":
            build_client_local(client, "worker")
        else:
            return "0"
    # This part is not necessary, functions can directly call the build_client_* functions.
    # I just wanted a central place to call the functions from.
    elif client is not None:
        role        = role
        location    = location
        if location == "aws":
            key  = models.Keys.query.get(client.id).aws
            build_client_aws(client, key)
        elif location == "digiocean":
            key = models.Keys.query.get(client.id).digiocean
            build_client_digiocean(client, key)
        elif location == "proxmox":
            build_client_local(client, "worker")

    else:
        return "0"

    return "1"


@app.route('/api/nodes/delete/<int:node_id>')
def node_delete(node_id):

    # Bash scripts to delete node

    # Database work
    node  = models.Nodes.query.get(node_id)
    if node.active is False:
        return "1"

    node.active = False
    node.date_rm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.session.add(node)
    db.session.commit()

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
    elif (os.path.isfile("managrr/provision/" + str(client_id) + ".worker.lockfile")):
        with open("managrr/provision/" + str(client_id) + ".worker.lockfile", 'r') as f:
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
    prevMonth = []
    results = []
    nodes = models.Nodes.query.all()

    today = datetime.date.today()
    for x in range(0, 5):
        prevMonth.append(today - relativedelta(months=x))
    for month in prevMonth:
        monthFormat = month.strftime("%Y%m")
        d = dict()
        d['month']  = month.strftime("%Y-%m")
        d['count']  = 0
        for node in nodes:
            nodeDateAdd = datetime.datetime.strptime(node.date_added, "%Y-%m-%d %H:%M:%S")
            if node.date_rm is not None:
                nodeDateRm  = datetime.datetime.strptime(node.date_rm, "%Y-%m-%d %H:%M:%S")
                nodeRmFormat  = nodeDateRm.strftime("%Y%m")
            nodeAddFormat = nodeDateAdd.strftime("%Y%m")
            if nodeAddFormat < monthFormat:
                if nodeRmFormat > monthFormat or node.date_rm is None:
                    d['count'] += 1
            elif nodeAddFormat == monthFormat:
                    d['count'] += 1
        results.insert(0, d)

    jsondumps = json.dumps(results, indent=4)

    return jsondumps


@app.route('/settings')
def settings_view():
    return render_template('settings.html', title="Settings")


def check_status(client_id, role="all"):
    if (role == "all"):
        if (os.path.isfile("managrr/provision/" + str(client_id) + ".lockfile")):
            return True
    if (role == "worker"):
        if (os.path.isfile("managrr/provision/" + str(client_id) + ".worker.lockfile")):
            return True
    return False


def build_client_local(client, role):
    if check_status(client.id) is True:
        return False

    hypervisorIP = models.Hypervisors.query.get(client.hyperv_id).IP
    lastVid = models.Nodes.query.order_by(models.Nodes.vid.desc()).filter_by(active=True).first()
    if lastVid is None:
        vid = 200
    else:
        vid = lastVid.vid + 1

    if (role == "all"):
        lastInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).filter_by(active=True).first()
        if lastInterface is None:
            inter = "vmbr10"
        else:
            inter = str(lastInterface.net)
            interid = re.split('(\d+)', inter)
            inter = "vmbr" + str(int(interid[1]) + 1)

    elif (role == "worker"):
        clientInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).filter(models.Nodes.client_id == client.id).first()
        inter = str(clientInterface.net)

    app.logger.info("Building: " + role + " for newclient " + client.name)
    arguments = "-c " + client.name + " -b " + str(client.id) + " -v " + str(vid) + " -r " + role + " -n " + hypervisorIP + " -i " + inter
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


def build_client_digiocean(client, key):
    app.logger.info("build_client_digiocean " + str(client.id) + key)
    return True


def build_client_aws(client, key):
    app.logger.info("build_client_aws " + str(client.id) + key)

    return True
