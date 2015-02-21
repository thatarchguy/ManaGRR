from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, SelectField, PasswordField
from wtforms.validators import DataRequired, Required, EqualTo
from managrr import models, db


class CreateNode(Form):
    location        = SelectField(u'Location', choices=[('proxmox', 'Local (Proxmox)'), ('digiocean', 'DigitalOcean'), ('aws', 'AWS')], validators=[DataRequired()])
    digiocean       = StringField(u'DOkey')
    aws             = StringField(u'awskey')


class AddClient(Form):
    name            = StringField(u'name', validators=[DataRequired()])
    email           = StringField(u'email', validators=[DataRequired()])
    phone           = StringField(u'phone', validators=[DataRequired()])
    size            = SelectField(u'size', choices=[('small', 'Small < 100'), ('medium', 'Medium 100-500'), ('large', 'Large 500-100'), ('xl', 'XL 1000+')], validators=[DataRequired()])
    digitalOcean    = StringField(u'DOkey')
    aws             = StringField(u'awskey')
    ssh             = StringField(u'sshkey')
    hyperv          = SelectField(u'hyperv')


class AddHyper(Form):
    location        = StringField(u'location', validators=[DataRequired()])
    ip              = StringField(u'ip', validators=[DataRequired()])


class SettingsPass(Form):
    currentPass     = PasswordField('currentpass', validators=[DataRequired()])
    newPass         = PasswordField('New Password', [Required(), EqualTo('newPassVerify', message='Passwords must match')])
    newPassVerify   = PasswordField('Repeat Password')


class SettingsGeneral(Form):
    email           = StringField(u'email', validators=[DataRequired()])
