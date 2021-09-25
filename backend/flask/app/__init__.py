import os
from flask import Flask

from app.website import website_blueprint
from app.api import api_blueprint
from app.api.database import Session


app = Flask(__name__)
app.config['SERVER_NAME'] = os.getenv('FQDN')

app.register_blueprint(api_blueprint, subdomain='api')
app.register_blueprint(website_blueprint, subdomain='www')
