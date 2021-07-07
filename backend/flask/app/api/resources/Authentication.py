import os
import string
import random
import requests
from flask_restful import Resource, reqparse
from flask import g, redirect
from sqlalchemy.exc import NoResultFound

from app.api.resources.util import validate_token, safe_str_cmp
from app.api.database.models.Authentication import StateToken, Authentication

__all__ = ['AuthenticateRedirect', 'Authenticate']


class AuthenticateRedirect(Resource):
    """
    url/prefix/authenticate
    """

    @staticmethod
    def get():
        parser = reqparse.RequestParser()
        parser.add_argument('state', location='args')
        parser.add_argument('code', location='args')
        args = parser.parse_args()
        if args.state and args.code:
            try:
                user, passed_state = args.state.split('-')
                state_query = g.session.query(StateToken).filter(StateToken.user == user)
                state = state_query.one().state
                if safe_str_cmp(state, passed_state):
                    state_query.delete(synchronize_session=False)  # Consume state
                    return AuthenticateRedirect.create_authentication(user, args.code)
                raise ValueError
            except NoResultFound:
                return {'message': 'Not expecting a request'}, 400
            except (AttributeError, IndexError, ValueError):
                return {'message': 'Invalid state'}
        else:
            return {'message': 'No state and/or code passed'}, 400

    @staticmethod
    def create_authentication(user, code):
        resp = requests.post(f"https://id.twitch.tv/oauth2/token"
                             f"?client_id={os.getenv('CLIENT_ID')}"
                             f"&client_secret={os.getenv('CLIENT_SECRET')}"
                             f"&code={code}"
                             f"&grant_type=authorization_code"
                             f"&redirect_uri={os.getenv('REDIRECT_URI')}")
        if resp.status_code != 200:
            return {'message': 'Invalid code'}, 400
        else:
            try:
                data = resp.json()
                # Get broadcaster_id using the /users endpoint and the token we just received
                resp = requests.get("https://api.twitch.tv/helix/users",
                                    headers={
                                        'Authorization': f'Bearer {data["access_token"]}',
                                        'Client-Id': os.getenv('CLIENT_ID')
                                    })
                userid = int(resp.json()['data'][0]['id'])
                authentication = Authentication(
                    user=user,
                    userid=userid,
                    accesstoken=data['access_token'],
                    refreshtoken=data['refresh_token'],
                    scope=data['scope'],
                    tokentype=data['token_type']
                )
                g.session.merge(authentication)
                g.session.commit()
                return {'message': 'success'}, 200
            except (ValueError, IndexError):
                return {'error': 'Something went wrong while creating an Authentication object.'}, 500


class Authenticate(Resource):
    """
    url/prefix/user/authenticate
    """
    @staticmethod
    def get(user):
        if user not in g.user_mapping:
            return {'message': 'Unknown user'}, 400
        if not validate_token(user):
            return {'error': 'Invalid token'}, 401

        state = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(30))
        g.session.merge(StateToken(user=user, state=state))
        g.session.commit()
        return redirect(f"https://id.twitch.tv/oauth2/authorize"
                        f"?client_id={os.getenv('CLIENT_ID')}"
                        f"&redirect_uri={os.getenv('REDIRECT_URI')}"
                        f"&response_type=code"
                        f"&scope={os.getenv('SCOPE')}"
                        f"&state={user}-{state}",
                        code=302)

    @staticmethod
    def refresh(user):
        """
        Refresh access token for user, return True if successful, False if not.
        """
        try:
            auth = g.session.query(Authentication).filter(Authentication.user == user).one()
        except NoResultFound:
            return False

        # Request new access token using refresh token
        resp = requests.post("https://id.twitch.tv/oauth2/token"
                             "?grant_type=refresh_token"
                             f"&refresh_token={auth.refreshtoken}"
                             f"&client_id={os.getenv('CLIENT_ID')}"
                             f"&client_secret={os.getenv('CLIENT_SECRET')}")

        if resp.status_code != 200:
            # Refresh unsuccessful
            return False

        # Update authentication token
        data = resp.json()
        auth.accesstoken = data['access_token']
        auth.refreshtoken = data['refresh_token']
        g.session.commit()
        return True
