from flask import g, Blueprint
from flask_restful import Api

from app.api.database import Session
from app.api.resources.Authentication import *
from app.api.resources.RandomSubscriberChallenge import *

api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint)


# ======== Add routes
api.add_resource(CheckToken, '/<string:user>/check-token')
api.add_resource(Authenticate, '/authenticate')
api.add_resource(Authenticate, '/authenticate/new-token')
api.add_resource(AuthenticateRedirect, '/twitch-redirect')

api.add_resource(Subscribers, '/<string:user>')
api.add_resource(CreateSubscriber, '/<string:user>/create')
# ========


@api_blueprint.before_request
def before_request():
    # Database session
    g.session = Session()


@api_blueprint.after_request
def after_request(response):
    if g.session is not None:
        g.session.commit()
        g.session.flush()
        g.session.close()
    return response
