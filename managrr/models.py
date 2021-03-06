from managrr import db
import datetime


class Nodes(db.Model):
    """
    Database Model for Nodes

    models.Nodes(client_id=1, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="10.5.0.103", net="vmbr20", vid="200")
    models.Nodes(client_id=models.Client.get(1)
    """
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    type = db.Column(db.String(20))
    date_added = db.Column(db.String(20))
    location = db.Column(db.String(30))
    IP = db.Column(db.String(20))
    net = db.Column(db.String(10))
    vid = db.Column(db.Integer)
    active = db.Column(db.Boolean, unique=False, default=True)
    date_rm = db.Column(db.String(20))

    def __repr__(self):
        return '<Type %r>' % (self.type)


class Hypervisors(db.Model):
    """
    Database Model for Hypervisorss

    models.Hypervisors(location="RACK14-2", IP="192.168.1.15", status="1")

    status codes:   0 - offline
                    1 - online
                    2 - maintenance
                    3 - oops
    """
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(30))
    IP = db.Column(db.String(20))
    status = db.Column(db.Integer)

    def __repr__(self):
        return '<Type %r>' % (self.type)


class Keys(db.Model):
    """
    Database Model for Keys

    models.Keys(aws='45uy34r78y8347tr38try', digiocean='jweklfjwer23ru2oejfowif02983r', ssh='weruiwehiurh7823rhywehfh2389r', client_id='1')
    """
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    digiocean = db.Column(db.String(64))
    aws = db.Column(db.String(64))
    ssh = db.Column(db.String(500))

    def __repr__(self):
        return '<Client: %r>' % (self.client_id)


class Jobs(db.Model):
    """
    Database model to hold running jobs from Redis
    You'd think redis would keep track of this...
    https://github.com/nvie/rq/issues/476
    You can't list jobs that are done / running
    You can however, get status information if you know the key

    I could of totally just handled all the status stuff here instead of in the job metadata. hmm
    """
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'),
                          primary_key=True)
    role = db.Column(db.String(16))
    job_key = db.Column(db.String(128))

    def __repr__(self):
        return '<Type: %r>' % (self.type)


class Clients(db.Model):
    """
    Database Model for Clients

    models.Clients(name="testClient", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), phone="555-555-555", email="contact@email.com", size="medium"))
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    date_added = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(30))
    size = db.Column(db.String(15))
    hyperv_id = db.Column(db.Integer, db.ForeignKey('hypervisors.id'))
    nodes = db.relationship('Nodes', backref='client', lazy='dynamic')
    keys = db.relationship('Keys', backref='client', lazy='dynamic')
    active = db.Column(db.Boolean, unique=False, default=True)
    date_rm = db.Column(db.String(20))

    def __repr__(self):
        return '<Name %r>' % (self.name)


class Users(db.Model):
    id = db.Column('user_id', db.Integer, primary_key=True)
    username = db.Column('username', db.String(20), unique=True, index=True)
    password = db.Column('password', db.String(40))
    email = db.Column('email', db.String(50), unique=True, index=True)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)
