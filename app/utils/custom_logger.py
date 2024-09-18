import inspect
import logging
import os
import threading
from fastapi import Request

thread_local = threading.local()

# Determine the environment from an environment variable
defaultEnvironment = 'local'
environment = os.getenv('ENVIRONMENT', defaultEnvironment)

# Ensure you clear the context when done processing a message
def clear_thread_local_context():
    if hasattr(thread_local, 'context'):
        del thread_local.context

# Extracted function to handle building context
def build_log_prefix(request: Request = None):
    parts = []

    if request:
        request_id = getattr(request.state, 'request_id', '')
        session_id = getattr(request.state, 'session_id', '')
        user_id = getattr(request.state, 'user_id', '')
        query_id = getattr(request.state, 'query_id', '')

        if request_id:
            parts.append(f"[request_id: {request_id}]")
        if session_id:
            parts.append(f"[session_id: {session_id}]")
        if user_id:
            parts.append(f"[user_id: {user_id}]")
        if query_id:
            parts.append(f"[query_id: {query_id}]")

    elif getattr(thread_local, 'context', None):
        thread_context = thread_local.context
        request_id = thread_context.get('request_id', '')
        session_id = thread_context.get('session_id', '')
        user_id = thread_context.get('user_id', '') or thread_context.get('userId', '')
        query_id = thread_context.get('query_id', '') or thread_context.get('queryId', '')

        if request_id:
            parts.append(f"[request_id: {request_id}]")
        if session_id:
            parts.append(f"[session_id: {session_id}]")
        if user_id:
            parts.append(f"[user_id: {user_id}]")
        if query_id:
            parts.append(f"[query_id: {query_id}]")

    return " ".join(parts)

class CustomLogger(logging.getLoggerClass()):
    def build_msg(self, msg, request: Request = None):
        prefix = build_log_prefix(request)
        return f"{prefix} {msg}" if prefix else msg

    def _log_with_stacklevel(self, level, msg, *args, request: Request = None, exc_info=None, **kwargs):
        msg = self.build_msg(msg, request)

        if exc_info:
            kwargs['exc_info'] = exc_info

        if 'stacklevel' not in kwargs:
            frame_info = inspect.stack()
            stacklevel = 2
            for i, frame in enumerate(frame_info):
                if 'custom_logger.py' not in frame.filename:
                    stacklevel = i + 1
                    break
            kwargs['stacklevel'] = stacklevel

        super().log(level, msg, *args, **kwargs)

    def info(self, msg, *args, request: Request = None, **kwargs):
        self._log_with_stacklevel(logging.INFO, msg, *args, request=request, **kwargs)

    def warning(self, msg, *args, request: Request = None, **kwargs):
        self._log_with_stacklevel(logging.WARNING, msg, *args, request=request, **kwargs)

    def error(self, msg, *args, request: Request = None, **kwargs):
        self._log_with_stacklevel(logging.ERROR, msg, *args, request=request, **kwargs)

    def debug(self, msg, *args, request: Request = None, **kwargs):
        self._log_with_stacklevel(logging.DEBUG, msg, *args, request=request, **kwargs)

    def critical(self, msg, *args, request: Request = None, **kwargs):
        self._log_with_stacklevel(logging.CRITICAL, msg, *args, request=request, **kwargs)

    def exception(self, msg, *args, request: Request = None, **kwargs):
        self._log_with_stacklevel(logging.ERROR, msg, *args, exc_info=True, request=request, **kwargs)

    # def info_with_event(self, msg, elapsed_time, processed_method, *args, request: Request = None, **kwargs):
    #     self._log_with_stacklevel(logging.INFO, msg, *args, request=request, **kwargs)
    #     self.log_event_to_posthog("info", elapsed_time, processed_method)
    #
    # def log_event_to_posthog(self, level, elapsed_time, processed_method):
    #     prefix_properties = {}
    #     clean_prefix = build_log_prefix().strip('[]')
    #     prefix_parts = clean_prefix.split('] [')
    #
    #     for part in prefix_parts:
    #         if ':' in part:
    #             key, value = part.split(':', 1)
    #             prefix_properties[key.strip()] = value.strip()
    #
    #     # Implement your PostHog event capture logic here

class ContextualFilter(logging.Filter):
    def filter(self, record):
        prefix = build_log_prefix()
        if prefix:
            record.msg = f"{prefix} {record.msg}"
        return True
