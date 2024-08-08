import functools
import uuid
from flask import request, g
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


def query_tracking_with_id(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query_id = request.args.get("query_id") or kwargs.get('query_id', "QUERY_ID_MISSING")
        user_id = request.args.get('user_id') or kwargs.get('user_id', "USER_ID_MISSING")
        session_id = g.get("session_id", "SESSION_ID_MISSING")

        g.query_id = query_id if query_id != "QUERY_ID_MISSING" else ""
        g.user_id = user_id if user_id != "USER_ID_MISSING" else ""
        backend_call_id = str(uuid.uuid4())
        g.backend_call_id = backend_call_id
        start_time = datetime.utcnow()
        # start_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"

        logger.info(f"START {request.method} /{request.endpoint} endpoint - call_id: {backend_call_id}  - user_id: {user_id} - session_id: {session_id} - query_id: {query_id} - start_time: {start_time_str}")
        result = func(*args, **kwargs)

        finish_time = datetime.utcnow()
        # finish_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"
        finish_time_str = finish_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] + " +0000"
        elapsed_time = (finish_time - start_time).total_seconds()

        logger.info(f"FINISH {request.method} /{request.endpoint} endpoint - call_id: {backend_call_id}  - user_id: {user_id} - session_id: {session_id} - query_id: {query_id} - finish_time: {finish_time_str} - elapsed_time: {elapsed_time:.2f} seconds")
        return result
    return wrapper


# def configure_exporter(exporter):
#     """Configures OpenTelemetry context propagation to use Cloud Trace context
#
#     Args:
#         exporter: exporter instance to be configured in the OpenTelemetry tracer provider
#     """
#     set_global_textmap(CloudTraceFormatPropagator())
#     tracer_provider = TracerProvider()
#     tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
#     trace.set_tracer_provider(tracer_provider)
#
#
# configure_exporter(CloudTraceSpanExporter())
# tracer = trace.get_tracer(__name__)


# def prepare_trace(func):
# @functools.wraps(func)
# def wrapper(*args, **kwargs):
#     span = trace.get_current_span()
#     if hasattr(g, "request_id"):
#         span.set_attribute("request_id", g.request_id)
#     if hasattr(g, "session_id"):
#         span.set_attribute("session_id", g.session_id)
#     if "user_id" in request.args:
#         span.set_attribute("user_id", request.args.get("user_id"))
#
#     if hasattr(span, 'attributes'):
#         logger.info(f"Span attributes: {span.attributes}")
#     logger.info(f"flask g object: {g.__dict__}")
#     logger.info(f"request object: {request.__dict__}")
#
#     return func(*args, **kwargs)
# return wrapper
