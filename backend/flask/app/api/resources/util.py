from datetime import datetime
from typing import Union, Tuple, Dict
from flask_restful import reqparse
from flask import g
from sqlalchemy.orm.exc import NoResultFound

from app.api.database import engine
from app.api.database.models import Base
from app.api.database.models.Authentication import User, Authentication

__all__ = ['get_all_tables', 'get_table', 'safe_str_cmp', 'validate_token', 'get_user_auth']


def get_all_tables() -> Dict[str, Base]:
    Base.metadata.reflect(engine)
    return Base.metadata.tables


def get_table(tablename: str) -> Union[Base, None]:
    """
    Get database table by tablename
    """
    try:
        return get_all_tables()[tablename]
    except KeyError:
        return None


def safe_str_cmp(str1: str, str2: str) -> bool:
    """
    Compare two strings in constant time, return True if equal, False if not
    """
    if type(str1) != str or type(str2) != str:
        return False
    return len(str1) == len(str2) and all([str1[i] == str2[i] for i in range(len(str1))])


def validate_token(user: str, verbose: bool = False) -> Union[bool, Tuple[bool, str, datetime]]:
    parser = reqparse.RequestParser()
    parser.add_argument('token', type=str, required=True)
    args = parser.parse_args()
    try:
        row = g.session.query(User).filter(User.username == user).one()
        token, last_purged = row.token, row.last_purged
    except NoResultFound:
        return (False, None, None) if verbose else False
    is_valid = safe_str_cmp(args.token, token)
    return (is_valid, token, last_purged) if verbose else is_valid


def get_user_auth(user: str, session=None) -> Union[Authentication, None]:
    """
    Retrieve Authentication object from the database for user,
    """
    try:
        session = session or g.session
        auth = session.query(Authentication).filter(Authentication.user == user).one()
    except NoResultFound:
        return None
    return auth
