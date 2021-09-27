import os
import re
import requests
from typing import Tuple, List, Union
from time import sleep
from datetime import datetime, timedelta
from flask_restful import Resource, reqparse
from flask import g
from uwsgidecorators import thread
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import select
from sqlalchemy.dialects.postgresql import insert

from app.logging import get_logger
from app.api.resources.util import validate_token, get_user_auth, get_table
from app.api.resources.Authentication import Authenticate
from app.api.database.models.Authentication import User

__all__ = ['Subscribers', 'CreateSubscriber']


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
    @thread  # uWSGI thread
    def purge_nonsubs(user: str, session: Session) -> None:
        """
        [DELETE] method
        Purge users from the database that are no longer subscribed.
        """
        logger = get_logger('remove_non_subs')
        logger.info(f"========== Called purge_nonsubs({user}) ==========")

        auth = get_user_auth(user, session=session)
        if auth is None:
            logger.error(f"No authentication object found for {user}")

        token_refreshed = False  # The token has been refreshed since the start of this request
        retry_503 = True
        subscribers = []
        cursor = None  # Pagination cursor: tells the server where to start fetching the next set of results
        done = False  # All subscribers retrieved from Twitch API
        while not done:  # Need subsequent requests to obtain more subscribers (max 100 per request)
            if token_refreshed:
                auth = get_user_auth(user, session=session)
                if auth is None:
                    logger.error(f"No authentication object found for {user}")

            resp = requests.get(f"https://api.twitch.tv/helix/subscriptions"
                                f"?broadcaster_id={auth.userid}"
                                f"&first=100" +
                                f"&after={cursor}" * (cursor is not None),
                                headers={
                                    'Authorization': f'Bearer {auth.accesstoken}',
                                    'Client-Id': os.getenv('CLIENT_ID')
                                })

            if resp.status_code == 400:
                logger.error('User must be a Twitch partner or affiliate.')
            elif resp.status_code == 401:
                # Unauthorized, try to refresh access token
                if token_refreshed:
                    # Access token is recently refreshed, but still not authorized
                    logger.critical("No valid access token available, please reauthorize application")
                refresh_successful = Authenticate.refresh(user, session=session)
                if refresh_successful:
                    token_refreshed = True
                    logger.info("Twitch oAuth token refreshed")
                    continue
                else:
                    logger.error(f"Could not refresh an unauthorized token, reautherize application")
            elif resp.status_code == 429:
                # Twitch API rate limit hit (800 / minute)
                sleep(2)
                continue
            elif resp.status_code == 503:
                # Retry once; if 503 again there probably is something wrong with the Twitch API
                if retry_503:
                    retry_503 = False
                    continue
                logger.error("Twitch API returned 503. Check https://devstatus.twitch.tv/")

            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError:
                logger.error(f"Twitch API responded with unexepected status code {resp.status_code}")
                return

            # Request successful
            data = resp.json()
            subscribers.extend([obj['user_name'].lower() for obj in data['data']])
            cursor = data['pagination'].get('cursor', None)
            if cursor is None:
                done = True

        table = get_table(user)
        if table is None:
            logger.error(f"User '{user}' does not have a table in postgres")
            return
        delete = table.delete().where(~table.c.twitch.in_(subscribers))
        result = session.execute(delete)
        session.query(User).filter(User.username == user).update({'last_purged': datetime.now()})
        session.commit()
        session.flush()
        logger.info(f"Succesfully removed {result.rowcount} non-subs.")


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
