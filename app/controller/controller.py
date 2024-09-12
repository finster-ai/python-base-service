# controller.py


import random
from time import sleep
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.model.api_error_response import ErrorDetail, ApiErrorResponse
from app.utils.api_utils import g_query_tracking_values_to_str, create_api_response
from app_instance import logger
from app.service import auth_service
from app.service.auth_service import requires_auth
from app.utils.wrappers import set_session_id, request_tracking_with_id
import traceback

# Create APIRouter instance
router = APIRouter(
    prefix="/api/v2",
    tags=["controller"],
)

# Error handling for AuthService.AuthError
@router.exception_handler(auth_service.AuthError)
async def handle_auth_error(request: Request, ex: auth_service.AuthError):
    error_detail = ErrorDetail(code=ex.status_code, message=ex.error)
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.exception(f"Authentication error for {g_query_tracking_values_to_str(request.state)} - ERROR: {ex}")
    return JSONResponse(status_code=ex.status_code, content=api_error_response.dict())

# Define error handlers for HTTPException
@router.exception_handler(HTTPException)
async def handle_blueprint_error(request: Request, e: HTTPException):
    error_detail = ErrorDetail(code=e.status_code, message=str(e.detail))
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.exception(f"Blueprint error for {g_query_tracking_values_to_str(request.state)} - ERROR: {e}")
    return JSONResponse(status_code=e.status_code, content=api_error_response.dict())

# Generic error handler
@router.exception_handler(Exception)
async def handle_generic_blueprint_error(request: Request, e: Exception):
    error_detail = ErrorDetail(code=500, message=str(e))
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.exception(f"Blueprint Generic error for {g_query_tracking_values_to_str(request.state)} - ERROR: {e}")
    return JSONResponse(status_code=500, content=api_error_response.dict())

# Public route
@router.get("/public")
@set_session_id
@request_tracking_with_id
async def public(request: Request):
    logger.info(f"You've reached the {request.url.path} endpoint")
    wait_time = random.uniform(1, 5)
    sleep(wait_time)
    response = create_api_response(f":A:A:A:A - You had to wait for {wait_time} seconds to see this.", request.state)
    return response

# Private route with authentication
@router.get("/private")
@requires_auth
@request_tracking_with_id
async def private(request: Request):
    try:
        raise ValueError("This is a test exception")
    except ValueError as e:
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="A ValueError occurred in /private endpoint")

# Another public route
@router.get("/public2")
@set_session_id
async def public2(request: Request):
    logger.info(f"You've reached the {request.url.path} endpoint")
    wait_time = random.uniform(1, 5)
    sleep(wait_time)
    response = create_api_response(f":A:A:A:A - You had to wait for {wait_time} seconds to see this.", request.state)
    return response

# Basic route
@router.get("/")
async def hello_world():
    return "Hello World!"
