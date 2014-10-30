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

class Clients(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(64), index=True, unique=True)
    date_added  = db.Column(db.String(20))
    nodes      = db.relationship('Nodes', backref='client',
                                   lazy='dynamic')
    def __repr__(self):
        return '<Name %r>' % (self.name)

#models.Clients(name="testClient", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

