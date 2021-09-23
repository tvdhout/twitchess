import os
import re
import requests
import logging
from typing import Tuple, List, Union
from time import sleep
from datetime import datetime, timedelta
from flask_restful import Resource, reqparse
from flask import g
from uwsgidecorators import thread
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import select
from sqlalchemy.dialects.postgresql import insert

from app.api.resources.util import validate_token, get_user_auth, get_table, get_all_tables
from app.api.resources.Authentication import Authenticate
from app.api.database.models.Authentication import User

__all__ = ['Subscribers', 'CreateSubscriber', 'delete_non_subs', 'delete_everyones_non_subs']
LOGGER = logging.getLogger(__name__)  # FIXME get logging working
os.makedirs('/logging', exist_ok=True)
file_handler = logging.FileHandler('/logging/remove_non_subs.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
LOGGER.addHandler(file_handler)
LOGGER.addHandler(stream_handler)


class Subscribers(Resource):
    @staticmethod
    def get(user: str) -> Union[List[str], Tuple[dict, int]]:
        """
        [GET] method
        Retrieve the Lichess usernames of all Twitch subscribers.
        """
        valid, _, last_purged = validate_token(user, verbose=True)
        if not valid:
            return {'error': 'Invalid token or user'}, 401
        table = get_table(user)
        if table is None:
            return {'message': 'User not in system'}, 400
        result = g.session.execute(select([table.c.lichess]))
        result = [row.lichess for row in result]
        if last_purged < (datetime.now() - timedelta(hours=12)):
            Subscribers.purge_nonsubs(user, g.session)
        return result

    @staticmethod
    @thread
    def purge_nonsubs(user: str, session: Session) -> Tuple[dict, int]:
        """
        [DELETE] method
        Purge users from the database that are no longer subscribed.
        TODO return and print statements to logging statements
        """
        print("Purging non-subs for", user)
        auth = get_user_auth(user, session=session)
        if auth is None:
            print(f'No authentication object found for {user}')

        token_refreshed = False  # The token has been refreshed since the start of this request
        retry_503 = True
        subscribers = []
        cursor = None  # Pagination cursor: tells the server where to start fetching the next set of results
        done = False  # All subscribers retrieved from Twitch API
        while not done:  # Need subsequent requests to obtain more subscribers (max 100 per request)
            if token_refreshed:
                auth = get_user_auth(user, session=session)
                if auth is None:
                    print(f'No authentication object found for {user}')

            resp = requests.get(f"https://api.twitch.tv/helix/subscriptions"
                                f"?broadcaster_id={auth.userid}"
                                f"&first=100" +
                                f"&after={cursor}" * (cursor is not None),
                                headers={
                                    'Authorization': f'Bearer {auth.accesstoken}',
                                    'Client-Id': os.getenv('CLIENT_ID')
                                })

            if resp.status_code == 400:
                print('User must be a Twitch partner or affiliate.')
            elif resp.status_code == 401:
                # Unauthorized, try to refresh access token
                if token_refreshed:
                    # Access token is recently refreshed, but still not authorized
                    return {'error': 'No valid access token available, please reauthorize application'}, 401
                refresh_successful = Authenticate.refresh(user, session=session)
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
            session.execute(delete)
        except NoResultFound:
            return {'message': 'No subscribers in the database to remove.'}, 200
        session.query(User).filter(User.username == user).update({'last_purged': datetime.now()})
        session.commit()
        session.flush()
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
            return f'{user} is not in the database. Authenticate online at twitchess.app/setup. ' \
                   f'Please notify te streamer.'

        try:
            stmt = insert(table).values(twitch=args.twitch.lower(),
                                        lichess=args.lichess.lower())
            stmt = stmt.on_conflict_do_update(
                constraint=f'{user}_pkey',
                set_=dict(lichess=args.lichess.lower())
            )
            g.session.execute(stmt)
            g.session.commit()
        except IntegrityError:
            return f'Error: Database error, please inform the developer at https://github.com/tvdhout/twitchess/issues '
        except Exception as e:
            return f'Unknown error: {str(e)[:75]}... please report at ' \
                   f'https://github.com/tvdhout/twitchess/issues '
        return f'Lichess name for @{args.twitch} set to {args.lichess}.'


def delete_non_subs(user: str, session: Session) -> Tuple[bool, dict]:
    """
    [DELETE] method
    Purge users from the database that are no longer subscribed.
    """
    auth = get_user_auth(user, session=session)
    if auth is None:
        return False, {'error': f'No authentication object found for {user}'}

    token_refreshed = False  # The token has been refreshed since the start of this request
    retry_503 = True
    subscribers = []
    cursor = None  # Pagination cursor: tells the server where to start fetching the next set of results
    done = False  # All subscribers retrieved from Twitch API
    while not done:  # Need subsequent requests to obtain more subscribers (max 100 per request)
        if token_refreshed:
            auth = get_user_auth(user, session)
            if auth is None:
                return False, {'error': f'No authentication object found for {user}'}

        resp = requests.get(f"https://api.twitch.tv/helix/subscriptions"
                            f"?broadcaster_id={auth.userid}"
                            f"&first=100" +
                            f"&after={cursor}" * (cursor is not None),
                            headers={
                                'Authorization': f'Bearer {auth.accesstoken}',
                                'Client-Id': os.getenv('CLIENT_ID')
                            })

        if resp.status_code == 400:
            return False, {'error': 'User must be a Twitch partner or affiliate.'}
        elif resp.status_code == 401:
            # Unauthorized, try to refresh access token
            if token_refreshed:
                # Access token is recently refreshed, but still not authorized
                return False, {'error': 'No valid access token available, please reauthorize application'}
            refresh_successful = Authenticate.refresh(user, session)
            if refresh_successful:
                token_refreshed = True
                continue
            else:
                return False, {'error': 'Could not refresh an unauthorized token, please reautherize application'}
        elif resp.status_code == 429:
            # Twitch API rate limit hit (800 / minute)
            sleep(2)
            continue
        elif resp.status_code == 503:
            # Retry once; if 503 again there probably is something wrong with the Twitch API
            if retry_503:
                retry_503 = False
                continue
            return False, {'error': 'Twitch API returned 503. Check https://devstatus.twitch.tv/'}

        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            return False, {'error': f'Twitch API responded with unexepected status code {resp.status_code}'}

        # Request successful
        data = resp.json()
        subscribers.extend([obj['user_name'].lower() for obj in data['data']])
        cursor = data['pagination'].get('cursor', None)
        if cursor is None:
            done = True

    try:
        table = get_table(user)
        if table is None:
            return False, {'message': 'User not in system'}
        delete = table.delete().where(~table.c.twitch.in_(subscribers))
        result = session.execute(delete)
        print(str(result))
    except NoResultFound:
        return True, {'message': 'No subscribers in the database to remove.'}
    return True, {'message': f'Succesfully removed non-subs.'}


def delete_everyones_non_subs(app_context, session_maker):
    """
    Purges non-subscribers from the database for every Twitchess-connected user.
    Args:
        app_context: Flask app_context, required to execute code in the flask process
        session_maker: SQLAlchemy session_maker, used to interact with postgres
    """
    with app_context():
        session = session_maker()
        tables = get_all_tables()
        for name in tables.keys():
            if name.lower() in ['login', 'authentication', 'states', 'stockvis']:
                continue
            success, message = delete_non_subs(name, session)
            LOGGER.info(f"{success} - {str(message)}")
            print(f"{success} - {str(message)}")
        session.commit()
        session.flush()
        session.close()
