# controller.py

import random
import asyncio  # Use asyncio for non-blocking sleep
from fastapi import APIRouter, Request, HTTPException

from app.service.auth_service import requires_auth
from app_instance import logger
from app.utils.api_utils import create_api_response


# Create APIRouter instance (equivalent to Flask's blueprint)
router = APIRouter(
    prefix="/api/v2",  # Add the prefix here as you did with Flask blueprints
    tags=["controller"],  # Optional: tag for the router
)

# Public route
@router.get("/public")
async def public(request: Request):
    logger.info(f"You've reached the {request.url.path} endpoint")
    logger.info(f"Request ID: {request.state.request_id}")
    logger.info(f"Session ID: {request.state.session_id}")
    wait_time = random.uniform(1, 5)
    await asyncio.sleep(wait_time)  # Use asyncio.sleep to avoid blocking
    response = create_api_response(f":A:A:A:A - You had to wait for {wait_time} seconds to see this.", request)
    return response

# Private route with authentication
@router.get("/private")
@requires_auth
# @request_tracking_with_id
async def private(request: Request):
    logger.info(f"You've SUCCESSFULLY GONE THROUGH AUTH for {request.url.path} endpoint")
    response = create_api_response(f"Returning PRIVATE ENDPOINT RESPONSE", request)
    return response


# Endpoint to test error responses
@router.get("/errortest")
async def private(request: Request):
    try:
        raise ValueError("This is a test exception")
    except ValueError as e:
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="A ValueError occurred in /private endpoint")


# Basic route
@router.get("/")
async def hello_world():
    return "Hello World!"
