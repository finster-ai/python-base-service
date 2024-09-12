import functools
import uuid
from flask import request, g
# from app_instance import logger, set_tracking_prefix
from app_instance import logger
from datetime import datetime


def set_session_id(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Adds session_id to g, creating it if it does not yet exist for the request"""
        session_id = request.args.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        g.session_id = session_id
        return func(*args, **kwargs)
    return wrapper


def request_tracking_with_id(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # query_id = request.args.get("query_id") or kwargs.get('query_id', "QUERY_ID_MISSING")
        # user_id = request.args.get('user_id') or kwargs.get('user_id', "USER_ID_MISSING")
        # session_id = g.get("session_id", "SESSION_ID_MISSING")
        query_id = request.args.get("query_id") or kwargs.get('query_id', "")
        user_id = request.args.get('user_id') or kwargs.get('user_id', "")
        session_id = g.get("session_id", "")
        request_id = str(uuid.uuid4())

        g.query_id = query_id if query_id != "QUERY_ID_MISSING" else ""
        g.user_id = user_id if user_id != "USER_ID_MISSING" else ""
        g.request_id = request_id

        start_time = datetime.utcnow()
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"

        logger.info(f"REQUEST PROCESSING STARTED - ENDPOINT: {request.method} {request.path} - START_TIME: {start_time_str}")
        result = func(*args, **kwargs)

        finish_time = datetime.utcnow()
        finish_time_str = finish_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"
        elapsed_time = (finish_time - start_time).total_seconds()

        logger.info(f"REQUEST PROCESSING FINISHED - ENDPOINT: {request.method} {request.path} - FINISH_TIME: {finish_time_str} - ELAPSED_TIME: {elapsed_time:.2f} seconds")
        return result
    return wrapper


