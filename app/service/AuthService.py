import json
from six.moves.urllib.request import urlopen
from functools import wraps

from flask import request, g
from jose import jwt
# import logging

from app.service.gcp_logging import logger
import os

# Initialize logger
# logger = logging.getLogger(__name__)

AUTH0_DOMAIN = None
API_AUDIENCE = None
ALGORITHMS = None
defaultEnvironment = None


# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def set_auth_config(domain, audience, algorithms, defenv):
    global AUTH0_DOMAIN, API_AUDIENCE, ALGORITHMS, defaultEnvironment
    AUTH0_DOMAIN = domain
    API_AUDIENCE = audience
    ALGORITHMS = algorithms
    defaultEnvironment = defenv


def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                             "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must start with"
                             " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                         "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must be"
                             " Bearer token"}, 401)

    token = parts[1]
    return token


# This checks if the JWT in Auth header is valid, decodes it and assigns the payload to g.current_user. If not it raises an authentication error
def requires_auth(f):
    """Determines if the Access Token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if the environment is local
        environment = os.getenv('FLASK_ENV', defaultEnvironment)
        if environment == 'local':
            logger.info("Local environment detected. Skipping authentication.")
            return f(*args, **kwargs)

        try:
            token = get_token_auth_header()
            jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
            jwks = json.loads(jsonurl.read())
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if rsa_key:
                try:
                    payload = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=ALGORITHMS,
                        audience=API_AUDIENCE,
                        issuer="https://"+AUTH0_DOMAIN+"/"
                    )
                    # logger.info(f"Token decoded successfully: {payload}")
                except jwt.ExpiredSignatureError:
                    raise AuthError({"code": "token_expired",
                                     "description": "token is expired"}, 401)
                except jwt.JWTClaimsError:
                    raise AuthError({"code": "invalid_claims",
                                     "description":
                                         "incorrect claims,"
                                         "please check the audience and issuer"}, 401)
                except Exception as e:
                    logger.error(f"Token parsing error: {e}")
                    raise AuthError({"code": "invalid_header",
                                     "description":
                                         "Unable to parse authentication"
                                         " token."}, 401)

                g.current_user = payload
                return f(*args, **kwargs)
            raise AuthError({"code": "invalid_header",
                             "description": "Unable to find appropriate key"}, 401)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthError({"code": "invalid_header",
                             "description": "Unable to parse authentication"" token."}, 401)
    return decorated
