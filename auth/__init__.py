import os
import json
from flask import request, _request_ctx_stack, session
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from models import User, UserAccount


AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']
API_AUDIENCE = os.environ['AUTH0_API_AUDIENCE']
ALGORITHMS = os.environ['JWT_ALGORITHMS'].split(',')

JWK = None  # This will store (on runtime) JWK to validate JWT

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise AuthError('Authorization header is not present.', 401)
    token_split = auth_header.split(' ')
    if len(token_split) != 2:
        raise AuthError('Malformed Authorization header value.', 401)
    return token_split[1]


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if not payload:
        token = get_token_auth_header()
        payload = verify_decode_jwt(token)
    if 'permissions' not in payload:
        raise AuthError('Permissions are not included in JWT', 403)
    if permission not in payload['permissions']:
        raise AuthError('You don\'t have permissions for this action', 403)
    return True


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    global JWK
    if not JWK:
        JWK = json.loads(urlopen('https://{}/.well-known/jwks.json'.format(AUTH0_DOMAIN)).read())
    try:
        payload = jwt.decode(token, JWK, ALGORITHMS, audience=API_AUDIENCE)
        return payload
    except Exception as e:
        raise AuthError(repr(e), 401)


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            if permission:
                check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator


def get_logged_user():
    try:
        token = get_token_auth_header()
        payload = verify_decode_jwt(token)
        oauth_id = payload['sub']
        # TODO: search user. If not found add it to DB
        user = User.query.filter(User.oauth_accounts.any(UserAccount.oauth_id == oauth_id)).first()
        if not user:
            user = User(name=oauth_id)
            user.insert()
            user_account = UserAccount(user_id=user.id, oauth_id=oauth_id)
            user_account.insert()
        return user
    except AuthError as ex:
        print(ex)
        return None
