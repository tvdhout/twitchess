from flask import g, Blueprint
from flask_restful import Api

from app.api.database import Session, user_mapping
from app.api.resources.Authentication import *
from app.api.resources.RandomSubscriberChallenge import *

api_blueprint = Blueprint('api', __name__)
api = Api(api_blueprint)


# ======== Add routes
api.add_resource(Authenticate, '/<string:user>/authenticate')
api.add_resource(AuthenticateRedirect, '/authenticate')

api.add_resource(Subscribers, '/<string:user>')
# ========


@api_blueprint.before_request
def before_request():
    # Database session
    g.session = Session()
    # Dict mapping user endpoints to their respective table
    g.user_mapping = user_mapping


@api_blueprint.after_request
def after_request(response):
    if g.session is not None:
        g.session.commit()
        g.session.flush()
        g.session.close()
    return response
