from flask import render_template, request, flash, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from managrr import app, db, models, login_manager, bcrypt, q
from .forms import CreateNode, AddClient, AddHyper, SettingsPass
from dateutil.relativedelta import relativedelta
import os
import datetime
import time
import subprocess
import re
import json
import socket


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login?next=' + request.path)


@login_manager.user_loader
def load_user(id):
    return models.Users.query.get(int(id))


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
@login_required
def index_view():

    # SQLAlchemy to get total clients
    clientCount = models.Clients.query.filter_by(active=True).count()
    hyperCount   = models.Hypervisors.query.count()

    return render_template('index.html',
                            title="Dashboard",
                            clientCount=clientCount,
                            hyperCount=hyperCount)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    password = bcrypt.generate_password_hash(request.form['password'])
    user = models.Users(request.form['username'], password, request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User: %s successfully registered' % user)
    return redirect(url_for('login_view'))


@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']
    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True
    registered_user = models.Users.query.filter_by(username=username).first()
    if registered_user and bcrypt.check_password_hash(registered_user.password, password):
        login_user(registered_user, remember=remember_me)
        flash('%s logged in successfully' % username)
        return redirect(request.args.get('next') or url_for('index_view'))
    flash('Username or Password is invalid', 'error')
    return redirect(url_for('login_view'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_view'))


@app.route('/hypervisors')
@login_required
def hypervisors_view():

    # SQLAlchemy functions here
    hypervisors = models.Hypervisors.query.all()

    return render_template('hypervisors.html', title="Hypervisors", entries=hypervisors)


@app.route('/hypervisors/add', methods=['POST', 'GET'])
@login_required
def hypervisor_add():
    error = None
    AddHyperForm = AddHyper()
    if AddHyperForm.validate_on_submit():
        if models.Hypervisors.query.filter_by(IP=AddHyperForm.ip.data).first() is None:
            newHypervisor = models.Hypervisors(location=AddHyperForm.location.data, IP=AddHyperForm.ip.data)
            db.session.add(newHypervisor)
            db.session.commit()
            hypervisor_check(newHypervisor.id)
            return redirect('/hypervisors')
        else:
            error = "Client IP is already in use"

    return render_template('addhyper.html', title="Add Hypervisor", AddHyperForm=AddHyperForm, error=error)


@app.route('/hypervisor/<int:hyperid>/check')
@login_required
def hypervisor_check(hyperid):
    hypervisor = models.Hypervisors.query.get(hyperid)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((hypervisor.IP, 8006))
        hypervisor.status = 1
        db.session.commit()
    except socket.error as e:
        print "Error on connect: %s" % e
        hypervisor.status = 0
        db.session.commit()
    s.close()

    return redirect(url_for('hypervisors_view'))


@app.route('/clients')
@login_required
def clients_view():

    # SQLAlchemy functions here
    clients = models.Clients.query.filter_by(active=True).all()
    hyperCount   = models.Hypervisors.query.count()

    return render_template('clients.html', title="Clients", entries=clients, hyperCount=hyperCount)


@app.route('/client/<int:client_id>/admin/')
@login_required
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
@login_required
def client_delete(client_id):
    client  = models.Clients.query.get(client_id)
    nodes   = models.Nodes.query.filter_by(client_id=client.id)
    keys    = models.Keys.query.filter_by(client_id=client.id).first()
    hypervisorIP    = models.Hypervisors.query.get(client.hyperv_id).IP

    if client.active is False:
        return redirect(url_for('index.view'))

    for node in nodes:
        if node.active is not False:
            node.active = False
            node.date_rm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.session.add(node)
            arguments = "-v " + str(node.vid) + " -r " + node.type + " -n " + hypervisorIP + " -i " + node.net
            subprocess.Popen(["bash delete.sh " + arguments], shell=True, executable="/bin/bash", cwd=os.getcwd() + "/provision/")

    client.active = False
    client.date_rm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.session.add(client)
    db.session.delete(keys)
    db.session.commit()
    app.logger.info("Deleted client: " + client.name)

    return redirect(url_for('index_view'))


@app.route('/client/<int:client_id>/admin/edit', methods=['POST'])
@login_required
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
@login_required
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

            job = q.enqueue(build_client, client)

            return redirect(url_for('client_admin', client_id=newClient.id, new_client=True))
        else:
            error = "Client Name is already in use"

    return render_template('addclient.html', title='Add Client', AddClientForm=AddClientForm, error=error)

# This function is only for creating workers
# the db and controller are only made through the build_client
@app.route('/api/nodes/create/', methods=['POST', 'GET'])
@login_required
def node_create(client=None, role=None, location=None):
    if request.method == 'POST':
        clientName  = request.form['client']
        location    = request.form['location']
        # HEY. Look at this. Why do these exist. wont that not work on elif location== below?
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
            job = q.enqueue(build_worker_aws, client, key)
        elif location == "digiocean":
            key = digiocean
            clientKey = models.Keys.query.filter_by(client_id=client.id).first()
            clientKey.digiocean = key
            app.logger.info("ClientKey Added: " + str(client.id) + "," + client.name + "," + location)
            db.session.commit()
            job = q.enqueue(build_worker_digiocean, client, key)
        elif location == "proxmox":
            job = q.enqueue(build_worker_local, client)
        else:
            return "0"
    # This part is not necessary, functions can directly call the build_worker_* functions.
    # I just wanted a central place to call the functions from that wasn't a web request
    elif client is not None:
        role        = role
        location    = location
        if location == "aws":
            key  = models.Keys.query.get(client.id).aws
            build_worker_aws(client, key)
        elif location == "digiocean":
            key = models.Keys.query.get(client.id).digiocean
            build_worker_digiocean(client, key)
        elif location == "proxmox":
            build_worker_local(client)

    else:
        return "0"

    return "1"


@app.route('/api/nodes/delete/<int:node_id>')
@login_required
def node_delete(node_id):

    node  = models.Nodes.query.get(node_id)
    if node.active is False:
        return "1"

    client  = models.Clients.query.get(node.client_id)
    hypervisorIP    = models.Hypervisors.query.get(client.hyperv_id).IP

    node.active = False
    node.date_rm = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.session.add(node)
    arguments = "-v " + str(node.vid) + " -r " + node.type + " -n " + hypervisorIP + " -i " + node.net
    subprocess.Popen(["bash delete.sh " + arguments], shell=True, executable="/bin/bash", cwd=os.getcwd() + "/provision/")
    db.session.commit()
    app.logger.info("Deleted node: " + str(node.id) + " " + node.type)
    return "1"


@app.route('/api/nodes/checkin/', methods=['GET'])
@login_required
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
@login_required
def client_status(client_id):
    if (os.path.isfile("provision/" + str(client_id) + ".lockfile")):
        with open("provision/" + str(client_id) + ".lockfile", 'r') as f:
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
    elif (os.path.isfile("provision/" + str(client_id) + ".worker.lockfile")):
        with open("provision/" + str(client_id) + ".worker.lockfile", 'r') as f:
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
@login_required
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


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    error = None
    ChangePassForm = SettingsPass()
    user = current_user
    if ChangePassForm.validate_on_submit():
        currentPass = request.form['currentPass']
        if bcrypt.check_password_hash(user.password, currentPass):
            newPass = bcrypt.generate_password_hash(request.form['newPass'])
            user.password = newPass
            db.session.add(user)
            db.session.commit()
            app.logger.info("Changed password for: " + user.username)
            return redirect('/settings')
        else:
            error = "Current password was incorrect"
    return render_template('settings.html', title="Settings", ChangePassForm=ChangePassForm, error=error)


def check_status(client_id, role="all"):
    if (role == "all"):
        if (os.path.isfile("provision/" + str(client_id) + ".lockfile")):
            return True
    if (role == "worker"):
        if (os.path.isfile("provision/" + str(client_id) + ".worker.lockfile")):
            return True
    return False


def build_client(client):
    if check_status(client.id) is True:
        return False

    hypervisorIP = models.Hypervisors.query.get(client.hyperv_id).IP
    lastVid = models.Nodes.query.order_by(models.Nodes.vid.desc()).filter_by(active=True).first()
    if lastVid is None:
        vid = 200
    else:
        vid = lastVid.vid + 1

    lastInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).filter_by(active=True).first()
    if lastInterface is None:
        inter = "vmbr10"
    else:
        inter = str(lastInterface.net)
        interid = re.split('(\d+)', inter)
        inter = "vmbr" + str(int(interid[1]) + 1)

    app.logger.info("Building: all for newclient " + client.name)
    arguments = "-c " + client.name + " -b " + str(client.id) + " -v " + str(vid) + " -r all -n " + hypervisorIP + " -i " + inter
    subprocess.Popen(["bash wrapper.sh " + arguments], shell=True, executable="/bin/bash", cwd=os.getcwd() + "/provision/")
    # Due to the nature of the database model, we need to insert basic information about nodes here.
    # They will be updated with ip address upon creation
    addDatabase = models.Nodes(client_id=client.id, type="database", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
    addControl  = models.Nodes(client_id=client.id, type="control", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid + 1)
    addWorker   = models.Nodes(client_id=client.id, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid + 2) 
    db.session.add(addDatabase)
    db.session.add(addControl)
    db.session.add(addWorker)
    db.session.commit()

    return True



def build_worker_local(client):
    if check_status(client.id) is True:
        return False
    hypervisorIP = models.Hypervisors.query.get(client.hyperv_id).IP
    lastVid = models.Nodes.query.order_by(models.Nodes.vid.desc()).filter_by(active=True).first()
    if lastVid is None:
        vid = 200
    else:
        vid = lastVid.vid + 1

    clientInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).filter(models.Nodes.client_id == client.id).first()
    inter = str(clientInterface.net)   

    app.logger.info("Building: worker for newclient " + client.name)
    arguments = "-c " + client.name + " -b " + str(client.id) + " -v " + str(vid) + " -r worker -n " + hypervisorIP + " -i " + inter
    subprocess.Popen(["bash wrapper.sh " + arguments], shell=True, executable="/bin/bash", cwd=os.getcwd() + "/provision/")

    addWorker = models.Nodes(client_id=client.id, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
    db.session.add(addWorker)
    db.session.commit()

    return True

def build_worker_digiocean(client, key):
    app.logger.info("build_client_digiocean " + str(client.id) + key)
    return True


def build_worker_aws(client, key):
    app.logger.info("build_client_aws " + str(client.id) + key)

    return True


def test_function():
    app.logger.info("Testing Queue")
    return True


@app.route('/testqueue')
def testqueue():
    job = q.enqueue(test_function)
  
    return "RAWR"
