from flask import render_template
from app import app
import datetime

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
    return render_template('index.html')


@app.route('/login')
def login_view():
    return render_template('login.html')
