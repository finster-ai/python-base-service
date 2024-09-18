import functools
import uuid
from fastapi import Request
from app_instance import logger
from datetime import datetime



# Decorator for tracking requests with additional information
def request_tracking_with_id(func):
    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        query_id = request.query_params.get("query_id") or kwargs.get('query_id', "")
        user_id = request.query_params.get('user_id') or kwargs.get('user_id', "")
        session_id = getattr(request.state, "session_id", "")
        request_id = str(uuid.uuid4())

        # Store additional tracking info in request.state for later use
        request.state.query_id = query_id
        request.state.user_id = user_id
        request.state.request_id = request_id

        start_time = datetime.utcnow()
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"

        logger.info(f"REQUEST PROCESSING STARTED - ENDPOINT: {request.method} {request.url.path} - START_TIME: {start_time_str}")
        result = await func(request, *args, **kwargs)

        finish_time = datetime.utcnow()
        finish_time_str = finish_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"
        elapsed_time = (finish_time - start_time).total_seconds()

        logger.info(f"REQUEST PROCESSING FINISHED - ENDPOINT: {request.method} {request.url.path} - FINISH_TIME: {finish_time_str} - ELAPSED_TIME: {elapsed_time:.2f} seconds")
        return result
    return wrapper


def manual_tracing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        # logger.info_with_event(f"METHOD PROCESSING STARTED: {func.__name__}")
        logger.info(f"METHOD PROCESSING STARTED: {func.__name__}")

        # Call the actual function
        result = func(*args, **kwargs)

        finish_time = datetime.utcnow()
        elapsed_time = (finish_time - start_time).total_seconds()

        # logger.info_with_event(f"METHOD PROCESSING FINISHED: {func.__name__} - ELAPSED_TIME: {elapsed_time:.5f} seconds", elapsed_time, func.__name__)
        logger.info(f"METHOD PROCESSING FINISHED: {func.__name__} - ELAPSED_TIME: {elapsed_time:.5f} seconds")
        return result
    return wrapper
