from flask import render_template, request, flash, redirect, url_for
from flask.ext.login import login_user, logout_user, current_user, login_required
from managrr import app, db, models, login_manager, bcrypt, q
from .forms import CreateNode, AddClient, AddHyper, SettingsPass, SettingsGeneral
from dateutil.relativedelta import relativedelta
from provision.provision import ClientClass
from rq import get_current_job
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
    hyperCount = models.Hypervisors.query.count()

    return render_template('index.html',
                           title="Dashboard",
                           clientCount=clientCount,
                           hyperCount=hyperCount)


"""
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
"""


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
    if registered_user and bcrypt.check_password_hash(registered_user.password,
                                                      password):
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

    hypervisors = models.Hypervisors.query.all()

    return render_template('hypervisors.html',
                           title="Hypervisors",
                           entries=hypervisors)


@app.route('/hypervisors/add', methods=['POST', 'GET'])
@login_required
def hypervisor_add():
    error = None
    AddHyperForm = AddHyper()
    if AddHyperForm.validate_on_submit():
        if models.Hypervisors.query.filter_by(
            IP=AddHyperForm.ip.data).first() is None:
            newHypervisor = models.Hypervisors(
                location=AddHyperForm.location.data,
                IP=AddHyperForm.ip.data)
            db.session.add(newHypervisor)
            db.session.commit()
            hypervisor_check(newHypervisor.id)
            return redirect('/hypervisors')
        else:
            error = "Client IP is already in use"

    return render_template('addhyper.html',
                           title="Add Hypervisor",
                           AddHyperForm=AddHyperForm,
                           error=error)


@app.route('/hypervisor/<int:hyperid>/check')
@login_required
def hypervisor_check(hyperid):
    hypervisor = models.Hypervisors.query.get(hyperid)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((hypervisor.IP, 8006))
        hypervisor.status = 1
        db.session.commit()
    except socket.error:
        hypervisor.status = 0
        db.session.commit()
    s.close()

    return redirect(url_for('hypervisors_view'))


@app.route('/clients')
@login_required
def clients_view():

    clients = models.Clients.query.filter_by(active=True).all()
    hyperCount = models.Hypervisors.query.count()

    return render_template('clients.html',
                           title="Clients",
                           entries=clients,
                           hyperCount=hyperCount)


@app.route('/client/<int:client_id>/admin/')
@login_required
def client_admin(client_id, new_client=False):
    new_client = request.args.get('new_client')
    new_worker = request.args.get('new_worker')
    client = models.Clients.query.get(client_id)
    nodes = client.nodes.filter_by(active=True).all()
    digikey = models.Keys.query.filter_by(client_id=client_id).first().digiocean
    awskey = models.Keys.query.filter_by(client_id=client_id).first().aws
    hypervisorIP = models.Hypervisors.query.get(client.hyperv_id).IP
    CreateNodeForm = CreateNode(digiocean=digikey, aws=awskey)
    ipaddr = (client.nodes.filter_by(type="control").first()).IP
    # If not specified, check to make sure there isn't a job
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
                           hypervisorIP=hypervisorIP,
                           ipaddr=ipaddr)


@app.route('/client/<int:client_id>/delete/')
@login_required
def client_delete(client_id):
    client = models.Clients.query.get(client_id)

    if client.active is False:
        return redirect(url_for('index.view'))

    clientObj = ClientClass(client)
    clientObj.delete_client()

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
    AddClientForm.hyperv.choices = [
        (a.IP, a.IP) for a in models.Hypervisors.query.order_by('IP')
    ]
    if AddClientForm.validate_on_submit():
        if models.Clients.query.filter_by(
            name=AddClientForm.name.data).first() is None:
            newClient = models.Clients(
                name=AddClientForm.name.data,
                date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                phone=AddClientForm.phone.data,
                email=AddClientForm.email.data,
                size=AddClientForm.size.data)

            hypervisor = models.Hypervisors.query.filter_by(
                IP=AddClientForm.hyperv.data).first()
            newClient.hyperv_id = hypervisor.id
            db.session.add(newClient)

            db.session.commit()
            clientKeys = models.Keys(aws=AddClientForm.aws.data,
                                     digiocean=AddClientForm.digitalOcean.data,
                                     ssh=AddClientForm.ssh.data,
                                     client_id=newClient.id)
            db.session.add(clientKeys)
            db.session.commit()

            if AddClientForm.aws.data != "":
                app.logger.info("ClientKey Added: [NEWCLIENT]" + str(
                    newClient.id) + "," + newClient.name + ",aws")
            if AddClientForm.digitalOcean.data != "":
                app.logger.info("ClientKey Added: [NEWCLIENT]" + str(
                    newClient.id) + "," + newClient.name + ",digiocean")
            if AddClientForm.ssh.data != "":
                app.logger.info("ClientKey Added: [NEWCLIENT]" + str(
                    newClient.id) + "," + newClient.name + ",ssh")

            client = models.Clients.query.get(newClient.id)
            clientObj = ClientClass(client)
            job = q.enqueue(clientObj.build_base, timeout=1000)
            jobDB = models.Jobs(client_id=client.id, job_key=job.id)
            db.session.add(jobDB)
            db.session.commit()

            return redirect(url_for('client_admin',
                                    client_id=newClient.id,
                                    new_client=True))
        else:
            error = "Client Name is already in use"

    return render_template('addclient.html',
                           title='Add Client',
                           AddClientForm=AddClientForm,
                           error=error)


# This function is only for creating workers
# the db and controller are only made through the build_client
@app.route('/api/nodes/create/', methods=['POST', 'GET'])
@login_required
def node_create(client=None, role=None, location=None):
    if request.method == 'POST':
        clientName = request.form['client']
        location = request.form['location']
        digiocean = request.form['digiocean']
        aws = request.form['aws']
        # This function was tested in python CLI. Seems to work.
        client = models.Clients.query.filter_by(name=clientName).first()
        clientObj = ClientClass(client)
        if location == "aws":
            key = aws
            clientKey = models.Keys.query.filter_by(client_id=client.id).first()
            clientKey.aws = key
            app.logger.info("ClientKey Added: " + str(client.id) + "," +
                            client.name + "," + location)
            db.session.commit()
            job = q.enqueue(clientObj.build_worker_aws, client, key)
            jobDB = models.Jobs(client_id=client.id, job_key=job.id, role="worker")
            db.session.add(jobDB)
            db.session.commit()
        elif location == "digiocean":
            key = digiocean
            clientKey = models.Keys.query.filter_by(client_id=client.id).first()
            clientKey.digiocean = key
            app.logger.info("ClientKey Added: " + str(client.id) + "," +
                            client.name + "," + location)
            db.session.commit()
            job = q.enqueue(clientObj.build_worker_digiocean, client, key)
            jobDB = models.Jobs(client_id=client.id, job_key=job.id, role="worker")
            db.session.add(jobDB)
            db.session.commit()
        elif location == "proxmox":
            job = q.enqueue(clientObj.build_worker_local, timeout=300)
            jobDB = models.Jobs(client_id=client.id, job_key=job.id, role="worker")
            db.session.add(jobDB)
            db.session.commit()

        else:
            return "0"
    # This part is not necessary, functions can directly call the build_worker_* functions.
    # I just wanted a central place to call the functions from that wasn't a web request
    elif client is not None:
        role = role
        location = location
        if location == "aws":
            key = models.Keys.query.get(client.id).aws
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

    node = models.Nodes.query.get(node_id)
    if node.active is False:
        return "1"

    client = models.Clients.query.get(node.client_id)
    clientObj = ClientClass(client)
    clientObj.delete_node(node)
    return "1"


@app.route('/api/nodes/checkin/', methods=['GET'])
@login_required
def node_checkin():
    clientName = request.args.get('client')
    role = request.args.get('role')
    ip = request.args.get('ip')

    # This function was tested in python CLI. Seems to work.
    clientID = models.Clients.query.filter_by(name=clientName).one().id

    # We only want the first one, right? Yeah? Ideally hm... This could mess up if cloud workers provision faster than proxmox workers.
    node = models.Nodes.query.filter_by(client_id=clientID,
                                        type=role,
                                        IP='0.0.0.0').one()
    node.IP = ip
    db.session.commit()
    app.logger.info(clientName + " " + role + " " + ip + " Checked in")

    # Some nonexistent error checking straight to ok
    status = "1"

    return status


@app.route('/client/<int:client_id>/status')
@login_required
def client_status(client_id):
    percent = "0"
    jobDB = models.Jobs.query.filter_by(client_id=client_id).first()
    if jobDB:
        job = q.fetch_job(jobDB.job_key)
        # Uses custom meta tags on python-rq jobs to get status
        if str(job.meta['progress']) == "sysprep":
            percent = "30"
        elif str(job.meta['progress']) == "proxmox":
            percent = "50"
        elif str(job.meta['progress']) == "installing":
            percent = "80"
        else:
            percent = "10"
    return percent


@app.route('/api/nodes/history')
@login_required
def node_history():
    """
    Gathers the previous 5 months, and counts the amount
    of nodes that were active during that month.
    """
    prevMonth = []
    results = []
    nodes = models.Nodes.query.all()

    today = datetime.date.today()
    for x in range(0, 5):
        prevMonth.append(today - relativedelta(months=x))
    for month in prevMonth:
        monthFormat = month.strftime("%Y%m")
        d = dict()
        d['month'] = month.strftime("%Y-%m")
        d['count'] = 0
        for node in nodes:
            nodeDateAdd = datetime.datetime.strptime(node.date_added,
                                                     "%Y-%m-%d %H:%M:%S")
            nodeAddFormat = nodeDateAdd.strftime("%Y%m")
            if nodeAddFormat < monthFormat:
                if node.date_rm is None:
                    d['count'] += 1
                if node.date_rm is not None:
                    nodeDateRm = datetime.datetime.strptime(
                        node.date_rm, "%Y-%m-%d %H:%M:%S")
                    nodeRmFormat = nodeDateRm.strftime("%Y%m")
                    if nodeRmFormat > monthFormat:
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
    user = current_user
    GeneralForm = SettingsGeneral(email=user.email)
    ChangePassForm = SettingsPass()
    if GeneralForm.validate_on_submit():
        email = request.form['email']
        user.email = email
        db.session.add(user)
        db.session.commit()
        app.logger.info("Changed email for: " + user.username)
        flash('Email successfully changed')
        return redirect('/settings')
    if ChangePassForm.validate_on_submit():
        currentPass = request.form['currentPass']
        if bcrypt.check_password_hash(user.password, currentPass):
            newPass = bcrypt.generate_password_hash(request.form['newPass'])
            user.password = newPass
            db.session.add(user)
            db.session.commit()
            app.logger.info("Changed password for: " + user.username)
            flash('Password successfully changed')
            return redirect('/settings')
        else:
            error = "Current password was incorrect"
    return render_template('settings.html',
                           title="Settings",
                           ChangePassForm=ChangePassForm,
                           GeneralForm=GeneralForm,
                           error=error)


def check_status(client_id, role="all"):
    if (role == "all"):
        jobDB = models.Jobs.query.filter(role != "worker").filter_by(client_id=client_id).first()
        if jobDB:
            job = q.fetch_job(jobDB.job_key)
            if job is not None:
                jobStatus = job.is_finished
                if jobStatus:
                    db.session.delete(jobDB)
                    db.session.commit()
                    return False
            else:
                db.session.delete(jobDB)
                db.session.commit()
                return False
            return True
    elif (role == "worker"):
        jobDB = models.Jobs.query.filter_by(client_id=client_id,
                                            role="worker").first()
        if jobDB:
            job = q.fetch_job(jobDB.job_key)
            if job is not None:
                if job.is_finished():
                    db.session.delete(jobDB)
                    db.session.commit()
                    return False
            else:
                db.session.delete(jobDB)
                db.session.commit()
                return False
            return True

    return False


def test_function():
    app.logger.info("Testing Queue")
    job = get_current_job()
    job.meta["client"] = 1
    print job.meta
    time.sleep(200)
    return True


@app.route('/testqueue')
def testqueue():
    queued_jobs = q.job_ids
    newjob = q.fetch_job(queued_jobs[0])
    print newjob.id
    newjob.meta['client'] = "1"
    newjob.meta['progress'] = "sysprep"
    newjob.meta['role'] = "all"
    newjob.save()
    return newjob.meta['client']
