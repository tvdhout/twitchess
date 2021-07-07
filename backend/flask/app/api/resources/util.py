from typing import Union, Tuple
from flask_restful import reqparse
from flask import g
from sqlalchemy.orm.exc import NoResultFound

from app.api.database.models.Authentication import Login, Authentication


def safe_str_cmp(str1: str, str2: str) -> bool:
    """
    Compare two strings in constant time, return True if equal, False if not
    """
    if type(str1) != str or type(str2) != str:
        return False
    return len(str1) == len(str2) and all([str1[i] == str2[i] for i in range(len(str1))])


def validate_token(user: str, return_token: bool = False) -> Union[bool, Tuple[bool, str]]:
    parser = reqparse.RequestParser()
    parser.add_argument('token', type=str, required=True)
    args = parser.parse_args()
    try:
        token = g.session.query(Login.token).filter(Login.username == user).one().token
    except NoResultFound:
        return False
    is_valid = safe_str_cmp(args.token, token)
    return (is_valid, token) if return_token else is_valid


def get_user_auth(user: str) -> Union[Authentication, None]:
    """
    Retrieve Authentication object from the database for user,
    """
    try:
        auth = g.session.query(Authentication).filter(Authentication.user == user).one()
    except NoResultFound:
        return None
    return auth
