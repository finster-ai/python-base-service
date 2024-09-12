#  auth_service.py

import json
import os
from six.moves.urllib.request import urlopen
from functools import wraps
from fastapi import Request, HTTPException, Depends
from jose import jwt
from app_instance import app, logger

AUTH0_DOMAIN = app.state['AUTH_DOMAIN']
API_AUDIENCE = app.state['AUTH_AUDIENCE']
ALGORITHMS = app.state['AUTH_ALGORITHMS']
defaultEnvironment = app.state['DEFAULT_ENVIRONMENT']

# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header(request: Request):
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization")
    if not auth:
        raise AuthError({"code": "authorization_header_missing", "description": "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header", "description": "Authorization header must start with Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header", "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header", "description": "Authorization header must be Bearer token"}, 401)

    return parts[1]

def requires_auth(f):
    """Determines if the Access Token is valid"""
    @wraps(f)
    async def decorated(request: Request, *args, **kwargs):
        environment = os.getenv('ENVIRONMENT', defaultEnvironment)
        if environment == 'local':
            logger.info("Local environment detected. Skipping authentication.")
            return await f(request, *args, **kwargs)

        try:
            token = get_token_auth_header(request)
            jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
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
                        issuer=f"https://{AUTH0_DOMAIN}/"
                    )
                except jwt.ExpiredSignatureError:
                    raise AuthError({"code": "token_expired", "description": "token is expired"}, 401)
                except jwt.JWTClaimsError:
                    raise AuthError({"code": "invalid_claims", "description": "incorrect claims, please check the audience and issuer"}, 401)
                except Exception as e:
                    logger.error(f"Token parsing error: {e}")
                    raise AuthError({"code": "invalid_header", "description": "Unable to parse authentication token."}, 401)

                request.state.current_user = payload
                return await f(request, *args, **kwargs)
            else:
                raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)

        except AuthError as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(status_code=e.status_code, detail=e.error)

    return decorated
