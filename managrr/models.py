from managrr import db
import datetime


class Nodes(db.Model):
    """
    Database Model for Nodes

    models.Nodes(client_id=1, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="10.5.0.103", net="vmbr20", vid="200")
    models.Nodes(client_id=models.Client.get(1)
    """
    id          = db.Column(db.Integer, primary_key=True)
    client_id   = db.Column(db.Integer, db.ForeignKey('clients.id'))
    type        = db.Column(db.String(20))
    date_added  = db.Column(db.String(20))
    location    = db.Column(db.String(30))
    IP          = db.Column(db.String(20))
    net         = db.Column(db.String(10))
    vid         = db.Column(db.Integer)
    active      = db.Column(db.Boolean, unique=False, default=True)
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
    id          = db.Column(db.Integer, primary_key=True)
    location    = db.Column(db.String(30))
    IP          = db.Column(db.String(20))
    status      = db.Column(db.Integer)


class Keys(db.Model):
    """
    Database Model for Keys

    models.Keys(aws='45uy34r78y8347tr38try', digiocean='jweklfjwer23ru2oejfowif02983r', ssh='weruiwehiurh7823rhywehfh2389r', client_id='1')
    """
    id          = db.Column(db.Integer, primary_key=True)
    client_id   = db.Column(db.Integer, db.ForeignKey('clients.id'))
    digiocean   = db.Column(db.String(64))
    aws         = db.Column(db.String(64))
    ssh         = db.Column(db.String(500))

    def __repr__(self):
        return '<Client: %r>' % (self.client_id)


class Clients(db.Model):
    """
    Database Model for Clients

    models.Clients(name="testClient", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), phone="555-555-555", email="contact@email.com", size="medium"))
    """
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(64), index=True, unique=True)
    date_added  = db.Column(db.String(20))
    phone       = db.Column(db.String(20))
    email       = db.Column(db.String(30))
    size        = db.Column(db.String(15))
    hyperv_id   = db.Column(db.Integer, db.ForeignKey('hypervisors.id'))
    nodes       = db.relationship('Nodes', backref='client',
                                   lazy='dynamic')
    keys        = db.relationship('Keys', backref='client',
                                   lazy='dynamic')
    active      = db.Column(db.Boolean, unique=False, default=True)

    def __repr__(self):
        return '<Name %r>' % (self.name)
