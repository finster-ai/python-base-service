# api_utils.py

import math
import os
import threading

from app_instance import logger
from app.service import auth_service
from app.model.api_response import ApiResponse
from app.model.api_error_response import ErrorDetail, ApiErrorResponse
from datetime import datetime
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4






# Error handling for AuthService.AuthError
async def custom_handle_auth_error(request: Request, ex: auth_service.AuthError):
    error_detail = ErrorDetail(code=ex.status_code, message=ex.error)
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.error(f"Authentication error for {g_query_tracking_values_to_str(request)} - ERROR: {ex}")
    return api_error_response.to_response()


# Define error handlers for HTTPException
async def custom_handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
    error_detail = ErrorDetail(code=exc.status_code, message=str(exc.detail))
    api_error_response = ApiErrorResponse(errors=[error_detail])
    logger.exception(f"HTTP error for {g_query_tracking_values_to_str(request)} - ERROR: {exc}")
    return api_error_response.to_response()


# Another generic handler
async def custom_handle_generic_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception occurred: {exc}", exc_info=True)
    error_detail = ErrorDetail(code=500, message=str(exc))
    api_error_response = ApiErrorResponse(errors=[error_detail])
    return api_error_response.to_response()


class RequestStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Check for both "request_id" and "requestId" in headers and query parameters
        request_id = (
                request.headers.get("request_id")
                or request.headers.get("requestId")
                or request.query_params.get("request_id")
                or request.query_params.get("requestId")
        )
        request.state.request_id = request_id if request_id else str(uuid4())
        # Check for both "session_id" and "sessionId" in headers and query parameters
        session_id = (
                request.headers.get("session_id")
                or request.headers.get("sessionId")
                or request.query_params.get("session_id")
                or request.query_params.get("sessionId")
        )
        request.state.session_id = session_id if session_id else str(uuid4())
        # Check for both "user_id" and "userId" in headers and query parameters
        user_id = (
                request.headers.get("user_id")
                or request.headers.get("userId")
                or request.query_params.get("user_id")
                or request.query_params.get("userId")
        )
        request.state.user_id = user_id if user_id else ''
        # Check for  "queryId" in path parameters
        request.state.query = request.query_params.get("query", '')
        # Check for agent in path
        agent_endpoints = [
            "/agent",
            "/agentexp",
            "/agentexpflash",
            "/agentexpgpt35turbo",
            "/agentexpgpt4omini",
            "/agentexpgpt4o",
            "/templates"
        ]
        request_path = request.url.path
        request.state.agent = ''  # Initialize the agent in request.state
        for endpoint in agent_endpoints:
            if request_path.startswith(endpoint):
                request.state.agent = endpoint.lstrip('/')  # Set agent as the part after '/'
                request.state.query_id = str(uuid4())
                break

        # Proceed with the request
        response = await call_next(request)
        return response







def create_api_response(response_data, request: Request):
    response = ApiResponse(
        timestamp=datetime.utcnow().isoformat(),
        request_id=getattr(request.state, "request_id", ""),
        query_id=getattr(request.state, "query_id", ""),
        user_id=getattr(request.state, "user_id", ""),
        session_id=getattr(request.state, "session_id", ""),
        total_pages=getattr(request.state, "total_pages", 1),
        total_elements=getattr(request.state, "total_elements", 0),
        current_page=getattr(request.state, "current_page", 1),
        page_size=getattr(request.state, "page_size", 10),
        data=response_data
    )
    return response.to_response()


def sorting(entry, request: Request):
    """Sorts the entry data based on query parameters for 'sort_by' and 'sort_order'."""
    sort_by = request.query_params.get('sort_by', 'created_at')  # Default sort by timestamp
    sort_order = request.query_params.get('sort_order', 'asc')  # Default sort order is ascending

    # Log a warning if the sort field is not present in any report entries
    if all(sort_by not in report for report in entry):
        logger.warning(f"Sort field '{sort_by}' not found in any report entries. Sorting may not work as expected.")

    reverse = (sort_order == 'desc')
    try:
        return sorted(entry, key=lambda x: x.get(sort_by) or '', reverse=reverse)
    except TypeError as e:
        logger.error(f"Sorting failed due to field having data of different types: {e}. "
                     f"This field '{sort_by}' needs to be standardized to sort properly.")
        return entry


def pagination(entry, request: Request):
    """Paginates the entry data based on query parameters for 'page' and 'page_size'."""
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))

    request.state.current_page = page
    request.state.page_size = page_size
    request.state.total_elements = len(entry)
    request.state.total_pages = math.ceil(len(entry) / page_size) if page_size > 0 else 1

    # Pagination logic
    if page == 0 and page_size == 0:
        paginated_entry = entry
    else:
        start = (page - 1) * page_size
        end = start + page_size
        paginated_entry = entry[start:end]

    return paginated_entry


def g_query_tracking_values_to_str(request: Request):
    """Generates a string from the tracking values for logging."""
    request_id = request.state.request_id if hasattr(request.state, "request_id") else "REQUEST_ID_MISSING"
    query_id = request.state.query_id if hasattr(request.state, "query_id") else "QUERY_ID_MISSING"
    user_id = request.state.user_id if hasattr(request.state, "user_id") else "USER_ID_MISSING"

    return f"call_id: {request_id}  - user_id: {user_id} - query_id: {query_id}"


def stream_and_remove_file(fp: str):
    """Streams file content as a generator and deletes the file afterwards."""
    with open(fp, 'rb') as f:
        yield from f

    delete_file_in_thread(fp)


def delete_file_in_thread(fp: str):
    """Deletes a file in a separate thread (non-blocking)."""
    thread = threading.Thread(target=os.remove, args=(fp,), daemon=True)
    thread.start()
