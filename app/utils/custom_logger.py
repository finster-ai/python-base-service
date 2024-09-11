import inspect
import logging
import os
import threading

from flask import g, has_request_context, request
import posthog  # Ensure posthog is imported and configured


thread_local = threading.local()

# Determine the environment from an environment variable
defaultEnvironment = 'local'
environment = os.getenv('FLASK_ENV', defaultEnvironment)


# Ensure you clear the context when done processing a message
def clear_thread_local_context():
    if hasattr(thread_local, 'context'):
        del thread_local.context

# Extracted function to handle building context
def build_log_prefix():
    parts = []

    # Existing context checks (for Flask's request context)
    if has_request_context():
        request_id = getattr(g, 'request_id', '')
        session_id = getattr(g, 'session_id', '')
        user_id = getattr(g, 'user_id', '')
        # user_id = (getattr(g, 'user_id', '') or
        #            getattr(g, 'userId', '') or
        #            request.args.get('user_id', '') or
        #            request.args.get('userId', '') or
        #            (request.json and request.json.get('user_id', '')) or
        #            (request.json and request.json.get('userId', '')))
        # user_id = request.args.get('user_id', '') or request.args.get('userId', '') or getattr(g, 'user_id', '') or
        #            getattr(g, 'userId', '')
        query_id = getattr(g, 'query_id', '') or getattr(g, 'queryId', '')

        if request_id:
            parts.append(f"[request_id: {request_id}]")
        if session_id:
            parts.append(f"[session_id: {session_id}]")
        if user_id:
            parts.append(f"[user_id: {user_id}]")
        if query_id:
            parts.append(f"[query_id: {query_id}]")

    # Check if the logger is running inside a thread with context set
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
    def build_msg(self, msg):
        prefix = build_log_prefix()
        return f"{prefix} {msg}" if prefix else msg

    def _log_with_stacklevel(self, level, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        if 'stacklevel' not in kwargs:
            # Dynamically calculate the stack level, skipping 'custom_logger.py'
            frame_info = inspect.stack()
            stacklevel = 2  # Start with the default stacklevel
            for i, frame in enumerate(frame_info):
                if 'custom_logger.py' not in frame.filename:  # Skip frames from custom_logger.py
                    stacklevel = i + 1  # Set the stack level to the first non-custom_logger.py frame
                    break
            kwargs['stacklevel'] = stacklevel

        super().log(level, msg, *args, **kwargs)

    # Standard logging methods
    def info(self, msg, *args, **kwargs):
        self._log_with_stacklevel(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log_with_stacklevel(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_with_stacklevel(logging.ERROR, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log_with_stacklevel(logging.DEBUG, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log_with_stacklevel(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log_with_stacklevel(logging.ERROR, msg, *args, exc_info=True, **kwargs)

    # Methods with PostHog event tracking
    def info_with_event(self, msg, elapsed_time, processed_method, *args, **kwargs):
        self._log_with_stacklevel(logging.INFO, msg, *args, **kwargs)
        self.log_event_to_posthog("info",  elapsed_time, processed_method)

    # def error_with_event(self, msg, *args, **kwargs):
    #     self._log_with_stacklevel(logging.ERROR, msg, *args, **kwargs)
    #     self.log_event_to_posthog("error", msg)


    def log_event_to_posthog(self, level, elapsed_time, processed_method):
        # Build a dictionary of context properties from the prefix
        prefix_properties = {}

        # Split on '] [' or leading/trailing square brackets to isolate key-value pairs
        clean_prefix = build_log_prefix().strip('[]')
        prefix_parts = clean_prefix.split('] [')

        # Loop through each part and split them by ':'
        for part in prefix_parts:
            if ':' in part:
                key, value = part.split(':', 1)
                prefix_properties[key.strip()] = value.strip()

        # Customize this as needed to send the event to PostHog
        posthog.capture(
            prefix_properties.get("user_id", "unknown_user"),  # Use user_id from context or default to unknown_user
            event="BE_" + level + "_LOG",
            properties={
                "environment": environment,
                "level": level,
                # "message": msg,  # The original message without prefix
                **prefix_properties,
                "query": getattr(g, 'query', ''),
                "elapsed_time": f"{elapsed_time:.5f} seconds",
                "agent": getattr(g, 'agent', ''),
                "processed_method": processed_method,# Include all context properties like request_id, session_id, etc.
            }
        )


# Custom Contextual Filter
class ContextualFilter(logging.Filter):
    def filter(self, record):
        prefix = build_log_prefix()

        # If there is any context information, prepend it to the log message
        if prefix:
            record.msg = f"{prefix} {record.msg}"

        return True
