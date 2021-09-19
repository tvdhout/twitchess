import os
from flask import Flask
from app.api import api_blueprint
from app.website import website_blueprint


app = Flask(__name__)
app.config['SERVER_NAME'] = os.getenv('FQDN')

app.register_blueprint(api_blueprint, subdomain='api')
app.register_blueprint(website_blueprint, subdomain='www')
