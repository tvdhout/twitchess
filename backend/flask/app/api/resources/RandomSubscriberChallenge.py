import os
import re
import requests
from typing import Tuple, List, Union
from flask_restful import Resource, reqparse
from flask import g
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import select
from sqlalchemy.dialects.postgresql import insert
from time import sleep

from app.api.resources.util import validate_token, get_user_auth, get_table
from app.api.resources.Authentication import Authenticate

__all__ = ['Subscribers', 'CreateSubscriber']


class Subscribers(Resource):
    @staticmethod
    def get(user: str) -> Union[List[str], Tuple[dict, int]]:
        """
        [GET] method
        Retrieve the Lichess usernames of all Twitch subscribers.
        """
        valid = validate_token(user)
        if not valid:
            return {'error': 'Invalid token or user'}, 401
        table = get_table(user)
        if table is None:
            return {'message': 'User not in system'}, 400
        result = g.session.execute(select([table.c.lichess]))
        result = [row.lichess for row in result]
        return result

    @staticmethod
    def delete(user: str) -> Tuple[dict, int]:
        """
        [DELETE] method
        Purge users from the database that are no longer subscribed.
        """
        valid, token = validate_token(user, return_token=True)
        if not valid:
            return {'error': 'Invalid token or user'}, 401

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
            table = get_table(user)
            if table is None:
                return {'message': 'User not in system'}, 400
            delete = table.delete().where(~table.c.twitch.in_(subscribers))
            g.session.execute(delete)
        except NoResultFound:
            return {'message': 'No subscribers in the database to remove.'}, 200
        return {'message': f'Succesfully removed non-subs.'}, 200


class CreateSubscriber(Resource):
    @staticmethod
    def get(user: str) -> str:
        """
        Add a new subscriber to the database.
        Return the message sent by nightbot as a response
        """
        if not validate_token(user):
            return f'Error: Invalid Twitchess token. Please notify the streamer.'
        parser = reqparse.RequestParser()
        parser.add_argument('twitch', type=str, required=True)
        parser.add_argument('lichess', type=str, required=True)
        args = parser.parse_args()

        if args.lichess == '':
            return f'@{args.twitch}: give your lichess username right after the command'
        if not re.match(r'^[A-Za-z][\w\d-]{1,19}$', args.lichess):
            return f'@{args.twitch}: {args.lichess} is not a valid lichess name.'

        table = get_table(user)
        if table is None:
            return f'{user} is not in the database. Authenticate online at twitchess.app/setup'

        try:
            stmt = insert(table).values(twitch=args.twitch.lower(),
                                        lichess=args.lichess.lower())
            stmt = stmt.on_conflict_do_update(
                constraint=f'{user}_pkey',
                set_=dict(lichess=args.lichess.lower())
            )
            g.session.execute(stmt)
            g.session.commit()
        except IntegrityError as e:
            return f'Error: Database error, please inform the developer at https://github.com/tvdhout/twitchess/issues '
        except Exception as e:
            return f'Unknown error: {str(e)[:75]}... please report at ' \
                   f'https://github.com/tvdhout/twitchess/issues '
        return f'Lichess name for @{args.twitch} set to {args.lichess}.'
