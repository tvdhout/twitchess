import os
import re
import requests
from typing import Tuple, List, Union
from flask_restful import Resource, reqparse
from flask import g
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from time import sleep

from app.api.resources.util import validate_token, get_user_auth
from app.api.resources.Authentication import Authenticate

__all__ = ['Subscribers', 'CreateSubscriber']


class Subscribers(Resource):
    @staticmethod
    def get(user: str) -> Union[List[str], Tuple[dict, int]]:
        """
        [GET] method
        Retrieve the Lichess usernames of all Twitch subscribers.
        """
        if user not in g.user_mapping:
            return {'message': 'Unknown user'}, 400
        valid = validate_token(user)
        if not valid:
            return {'error': 'Invalid token'}, 401
        result = g.session.query(g.user_mapping[user].lichess).all()
        result = [row.lichess for row in result]
        return result

    @staticmethod
    def delete(user: str) -> Tuple[dict, int]:
        """
        [DELETE] method
        Purge users from the database that are no longer subscribed.
        """
        if user not in g.user_mapping:
            return {'message': 'Unknown user'}, 400
        valid, token = validate_token(user, return_token=True)
        if not valid:
            return {'error': 'Invalid token'}, 401

        auth = get_user_auth(user)
        if auth is None:
            return {'error': f'No authentication object found for {user}'}, 401

        token_refreshed = False  # The token has been refreshed since the start of this request
        retry_503 = True
        subscribers = []
        cursor = None  # Pagination cursor: tells the server where to start fetching the next set of results
        done = False  # All subscribers retrieved from Twitch API
        while not done:  # Need subsequent requests to obtain more subscribers (max 100 per request)
            if token_refreshed:
                auth = get_user_auth(user)
                if auth is None:
                    return {'error': f'No authentication object found for {user}'}, 401

            resp = requests.get(f"https://api.twitch.tv/helix/subscriptions"
                                f"?broadcaster_id={auth.userid}"
                                f"&first=100" +
                                f"&after={cursor}" * (cursor is not None),
                                headers={
                                    'Authorization': f'Bearer {auth.accesstoken}',
                                    'Client-Id': os.getenv('CLIENT_ID')
                                })

            if resp.status_code == 400:
                return {'error': 'User must be a Twitch partner or affiliate.'}, 400
            elif resp.status_code == 401:
                # Unauthorized, try to refresh access token
                if token_refreshed:
                    # Access token is recently refreshed, but still not authorized
                    return {'error': 'No valid access token available, please reauthorize application'}, 401
                refresh_successful = Authenticate.refresh(user)
                if refresh_successful:
                    token_refreshed = True
                    print("Token refreshed")
                    continue
                else:
                    return {'error': 'Could not refresh an unauthorized token, please reautherize application'}, 401
            elif resp.status_code == 429:
                # Twitch API rate limit hit (800 / minute)
                sleep(2)
                continue
            elif resp.status_code == 503:
                # Retry once; if 503 again there probably is something wrong with the Twitch API
                if retry_503:
                    retry_503 = False
                    continue
                return {'error': 'Twitch API returned 503. Check https://devstatus.twitch.tv/'}, 503

            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                return {'error': f'Twitch API responded with unexepected status code {resp.status_code}'}, 500

            # Request successful
            data = resp.json()
            subscribers.extend([obj['user_name'].lower() for obj in data['data']])
            cursor = data['pagination'].get('cursor', None)
            if cursor is None:
                done = True

        try:
            subs_to_purge = g.session.query(g.user_mapping[user]).filter(~g.user_mapping[user].twitch.in_(subscribers))
            nr_purged = subs_to_purge.count()
            if nr_purged > 0:
                subs_to_purge.delete(synchronize_session=False)
        except NoResultFound:
            return {'message': 'No subscribers in the database to remove.'}, 200

        return {'message': f'Succesfully removed {nr_purged} non-subs.'}, 200


class CreateSubscriber(Resource):
    @staticmethod
    def get(user: str) -> Union[List[str], Tuple[dict, int]]:
        """
        [POST] method
        Add a new subscriber to the database.
        """
        if user not in g.user_mapping:
            return {'message': 'Unknown user'}, 200
        if not validate_token(user):
            return {'error': 'Invalid token'}, 200
        parser = reqparse.RequestParser()
        parser.add_argument('twitch', type=str, required=True)
        parser.add_argument('lichess', type=str, required=True)
        args = parser.parse_args()

        if args.lichess == '':
            return {'message': f'{args.twitch} enter your lichess username after the command: !lichess username'}, 200
        if not re.match(r'^[A-Za-z][\w\d-]{1,19}$', args.lichess):
            return {'message': f'{args.twitch}: {args.lichess} is not a valid lichess name.'}, 200

        subscriber = g.user_mapping[user](
            twitch=args.twitch.lower(),
            lichess=args.lichess.lower()
        )

        try:
            g.session.merge(subscriber)
            g.session.commit()
        except IntegrityError as e:
            return {'IntegrityError': str(e)}, 400
        except Exception as e:
            return {'error': str(e)}, 500
        return {'message': f'lichess name for {args.twitch} set to {args.lichess}.'}, 201
