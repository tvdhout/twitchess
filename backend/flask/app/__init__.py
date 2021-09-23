import os
import atexit
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from app.website import website_blueprint
from app.api import api_blueprint
from app.api.database import Session
from app.api.resources.RandomSubscriberChallenge import delete_everyones_non_subs


app = Flask(__name__)
app.config['SERVER_NAME'] = os.getenv('FQDN')

app.register_blueprint(api_blueprint, subdomain='api')
app.register_blueprint(website_blueprint, subdomain='www')


# Remove non-subscribers from the user tables every 12 hours.
scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_everyones_non_subs, kwargs={'app_context': app.app_context, 'session_maker': Session},
                  trigger='interval', hours=12)
scheduler.start()
print("=================> started scheduler.")

atexit.register(scheduler.shutdown)  # Shut down scheduler when app closes
