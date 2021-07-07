import os
from flask import Flask
from app.api import api_blueprint


app = Flask(__name__)
app.config['SERVER_NAME'] = os.getenv('FQDN')

app.register_blueprint(api_blueprint)
