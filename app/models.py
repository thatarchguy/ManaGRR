from app import db
import datetime

class Nodes(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    client_id   = db.Column(db.Integer, db.ForeignKey('clients.id'))
    type        = db.Column(db.String(20))
    location    = db.Column(db.String(30))
    IP          = db.Column(db.String(20))   



    def __repr__(self):
        return '<Type %r>' % (self.type)
#models.Nodes(client_id=1, type="worker", location="proxmox", IP="10.5.0.103")
#models.Nodes(client_id=models.Client.get(1)

class Clients(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(64), index=True, unique=True)
    date_added  = db.Column(db.String(20))
    phone       = db.Column(db.String(20))
    email       = db.Column(db.String(30))
    size        = db.Column(db.String(15))
    nodes       = db.relationship('Nodes', backref='client',
                                   lazy='dynamic')
    def __repr__(self):
        return '<Name %r>' % (self.name)

#models.Clients(name="testClient", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), phone="555-555-555", email="contact@email.com", size="medium"))

