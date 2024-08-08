
import logging
import random
from time import sleep
from flask import Blueprint, jsonify, g, Response, request, stream_with_context

from app.model.api_error_response import ErrorDetail, ApiErrorResponse
from app.utils.api_utils import g_query_tracking_values_to_str, create_api_response
from app_instance import app, logger
from flask import Blueprint, jsonify
from flask_cors import cross_origin
from app.service import AuthService
from app.service.AuthService import requires_auth
from app.utils.wrappers import set_session_id, query_tracking_with_id
from werkzeug.exceptions import HTTPException


# Initialize the logger
logger = logging.getLogger(__name__)

# Create a Blueprint named 'controller'
controller_blueprint = Blueprint('controller', __name__)
url_prefix_controller = '/api/v2'


# Register the error handler for the AuthService.AuthError
@app.errorhandler(AuthService.AuthError)
def handle_auth_error(ex):
    error_detail = ErrorDetail(code=ex.status_code, message=ex.error)
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.error(f"Authentication error for " + g_query_tracking_values_to_str(g) + f" - ERROR: {ex}")
    return api_error_response.to_response()


# Define error handlers specifically for the blueprint
@controller_blueprint.errorhandler(HTTPException)
def handle_blueprint_error(e):
    error_detail = ErrorDetail(code=e.code, message=str(e))
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.error(f"Blueprint error for " + g_query_tracking_values_to_str(g) + f" - ERROR: {e}")
    return api_error_response.to_response()


@controller_blueprint.errorhandler(Exception)
def handle_generic_blueprint_error(e):
    error_detail = ErrorDetail(code=500, message=str(e))
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.error(f"Blueprint Generic error for " + g_query_tracking_values_to_str(g) + f" - ERROR: {e}")
    return api_error_response.to_response()


# Define routes within the Blueprint
@controller_blueprint.route("/public")
@cross_origin(headers=["Content-Type", "Authorization"])
@set_session_id
@query_tracking_with_id
def public():
    logger.info("You've reached the " + request.endpoint + " endpoint")
    # Generate a random wait time between 1 and 5 seconds
    wait_time = random.uniform(1, 5)
    sleep(wait_time)
    # response = jsonify(":A:A:A:A - You had to wait for " + str(wait_time) + " seconds to see this.")
    # response.headers.add("Access-Control-Allow-Origin", "*")
    # response.headers.add("ContentType", "application/json")
    # logger.info("FINISHED - You've reached the " + request.endpoint + " endpoint")

    response = create_api_response(":A:A:A:A - You had to wait for " + str(wait_time) + " seconds to see this.", g)
    return response


@controller_blueprint.route("/private")
@cross_origin(headers=["Content-Type", "Authorization"])
@requires_auth
@query_tracking_with_id
def private():
    try:
        # Intentionally raise an exception to test error handling
        raise ValueError("This is a test exception")
        response = "Hello from a private endpoint! You had to be authenticated to access to see this."
        return jsonify(message=response)
    except ValueError as e:
        # Log the error and raise a new HTTPException
        logger.error(f"An error occurred: {e}")
        error = HTTPException(description="A ValueError occurred in /private endpoint")
        error.code = 500  # Add a status code
        raise error


@controller_blueprint.route("/")
def hello_world():
    return "Hello World!"

