from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired
from app import models, db

class CreateNode(Form):
    locations = SelectField(u'Location', choices=[('proxmox','Local (Proxmox)'), ('digiocean','DigitalOcean'), ('aws','AWS')], validators=[DataRequired()])
    digitalOcean = StringField(u'DOkey') 
    aws = StringField(u'awskey') 
