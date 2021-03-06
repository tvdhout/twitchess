import os
import string
import random
import requests
from datetime import datetime, timedelta
from typing import Union, Tuple
from flask_restful import Resource, reqparse
from flask import g, redirect, Response
from sqlalchemy.exc import NoResultFound
from sqlalchemy import or_

from app.api.resources.util import validate_token, get_user_auth, error
from app.api.database import engine
from app.api.database.models.Authentication import Authentication, User, StateToken
from app.api.database.models.RandomSubscriberChallenge import make_subscriber_table, Base

__all__ = ['CheckAuthentication', 'AuthenticateRedirect', 'Authenticate', 'NewToken']


class CheckAuthentication(Resource):
    """
    Endpoint /<user>/check-auth
    Check if the given token is correct
    """
    @staticmethod
    def get(user: str) -> Tuple[Union[dict, str], int]:
        valid = validate_token(user=user)
        if valid:
            auth = get_user_auth(user)
            if auth is None:
                return {'valid': False}, 200
            if user == 'stockvis':  # stockvis, the developer, is exempt for testing purposes
                return {'valid': True}, 200

            resp = requests.get(f"https://api.twitch.tv/helix/subscriptions"
                                f"?broadcaster_id={auth.userid}",
                                headers={
                                    'Authorization': f'Bearer {auth.accesstoken}',
                                    'Client-Id': os.getenv('CLIENT_ID')
                                })
            try:
                resp.raise_for_status()
                return {'valid': True}, 200
            except requests.exceptions.HTTPError:
                return {'valid': False}, 200
        return {'valid': False}, 200


class AuthenticateRedirect(Resource):
    """
    Endpoint /twitch-redirect
    Twitch oauth redirects here and passes the state given in the request and the code to request an API token
    """

    @staticmethod
    def get() -> Union[Tuple[Union[dict, str], int], Response]:
        parser = reqparse.RequestParser()
        parser.add_argument('state', location='args', type=str)
        parser.add_argument('code', location='args', type=str)
        args = parser.parse_args()
        if args.state and args.code:
            try:
                states = [s.state for s in g.session.query(StateToken.state).all()]
                if args.state in states:
                    g.session.query(StateToken).filter(or_(
                        StateToken.state == args.state,
                        StateToken.datetime < (datetime.now() - timedelta(minutes=30))
                    )).delete(synchronize_session=False)  # Delete this state & stale states
                    data, code = AuthenticateRedirect.create_authentication(args.code)
                    if code == 201:
                        authentication = data['authentication']
                        username = data['username']

                        # Test the authentication and check if user is a Twitch partner / affiliate
                        resp = requests.get(f"https://api.twitch.tv/helix/subscriptions"
                                            f"?broadcaster_id={authentication.userid}",
                                            headers={
                                                'Authorization': f'Bearer {authentication.accesstoken}',
                                                'Client-Id': os.getenv('CLIENT_ID')
                                            })

                        # Not a Twitch partner or affiliate (stockvis, the developer, is exempt for testing purposes)
                        if resp.status_code == 400 and username != 'stockvis':
                            g.session.query(Authentication).filter(Authentication.userid == authentication.userid)\
                                .delete()
                            return redirect(f'https://www.twitchess.app/not-eligible')

                        make_subscriber_table(username)
                        Base.metadata.create_all(bind=engine)

                        try:
                            user = g.session.query(User).filter(User.username == username).one()
                        except NoResultFound:
                            login_token = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits)
                                                  for _ in range(40))
                            user = User(
                                username=username,
                                token=login_token
                            )
                            g.session.merge(user)
                            g.session.commit()
                        return redirect(f'https://www.twitchess.app/setup?user={username}&token={user.token}')

                raise ValueError
            except AttributeError:
                return error("[AuthenticateRedirect] Not expecting a request")
            except (IndexError, ValueError):
                return error("[AuthenticateRedirect] Invalid state")
        else:
            return error("[AuthenticateRedirect] No state and/or code passed")

    @staticmethod
    def create_authentication(code: str) -> Union[Tuple[Union[dict, str], int], Response]:
        resp = requests.post(f"https://id.twitch.tv/oauth2/token"
                             f"?client_id={os.getenv('CLIENT_ID')}"
                             f"&client_secret={os.getenv('CLIENT_SECRET')}"
                             f"&code={code}"
                             f"&grant_type=authorization_code"
                             f"&redirect_uri={os.getenv('REDIRECT_URI')}")
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            return error("[AuthenticateRedirect] Invalid code")
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
                login = str(resp.json()['data'][0]['login']).lower()
                authentication = Authentication(
                    user=login,
                    userid=userid,
                    accesstoken=data['access_token'],
                    refreshtoken=data['refresh_token'],
                    scope=data['scope'],
                    tokentype=data['token_type']
                )
                g.session.merge(authentication)
                g.session.commit()
                return {'username': login,
                        'authentication': authentication}, 201
            except (ValueError, IndexError):
                return error("[AuthenticateRedirect] Something went wrong while creating an Authentication object")


class NewToken(Resource):
    """
    Endpoint /<user>/new-token
    Create and return a new Twitchess token for <user>
    """

    @staticmethod
    def get(user) -> Response:
        valid, token, _ = validate_token(user, verbose=True)
        if valid:
            token = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits)
                                  for _ in range(40))
            user_obj = User(
                username=user,
                token=token
            )
            g.session.merge(user_obj)
            g.session.commit()
            return redirect(f'https://www.twitchess.app/setup?user={user}&token={token}')
        return error("Invalid token when requesting a new token.")


class Authenticate(Resource):
    """
    Endpoint /authenticate
    """

    @staticmethod
    def get(redirect_uri: str = os.getenv('REDIRECT_URI')) -> Union[Tuple[Union[dict, str], int], Response]:
        state = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(64))
        g.session.merge(StateToken(state=state))
        g.session.commit()
        return redirect(f"https://id.twitch.tv/oauth2/authorize"
                        f"?client_id={os.getenv('CLIENT_ID')}"
                        f"&redirect_uri={redirect_uri}"
                        f"&response_type=code"
                        f"&scope={os.getenv('SCOPE')}"
                        f"&state={state}",
                        code=302)

    @staticmethod
    def refresh(user: str, session=None) -> bool:
        """
        Refresh access token for user, return True if successful, False if not.
        """
        session = session or g.session
        try:
            auth = session.query(Authentication).filter(Authentication.user == user).one()
        except NoResultFound:
            return False

        # Request new access token using refresh token
        resp = requests.post("https://id.twitch.tv/oauth2/token"
                             "?grant_type=refresh_token"
                             f"&refresh_token={auth.refreshtoken}"
                             f"&client_id={os.getenv('CLIENT_ID')}"
                             f"&client_secret={os.getenv('CLIENT_SECRET')}")

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            # Refresh unsuccessful
            return False
        else:
            # Update authentication token
            data = resp.json()
            auth.accesstoken = data['access_token']
            auth.refreshtoken = data['refresh_token']
            session.commit()
            return True
