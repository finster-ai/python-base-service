import logging
import sys
import json
import os
import warnings


# Fetch environment variables
cluster_name = os.getenv('CLUSTER_NAME', 'unknown-cluster')
location = os.getenv('LOCATION', 'unknown-location')
namespace_name = os.getenv('NAMESPACE_NAME', 'unknown-namespace')
pod_name = os.getenv('POD_NAME', 'unknown-pod')
project_id = os.getenv('PROJECT_ID', 'unknown-project')

loglevel = 'info'
errorlog = '-'  # Log to stderr
accesslog = '-'  # Log to stdout
accesslog = None  # Disable access log

class LevelBasedFilter(logging.Filter):
    def __init__(self, level, name=""):
        super().__init__(name)
        self.level = level

    def filter(self, record):
        return record.levelno <= self.level


class JsonFormatter(logging.Formatter):
    def format(self, record):
        # Ensure that the message is fully formatted with any additional arguments
        record.message = record.getMessage()
        # Now build the log message with the file name and line number
        message = f"[{record.filename}:{record.lineno}] {record.message}"

        log_record = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            # 'message': record.getMessage(),
            'message': message,
            'filename': record.filename,
            'lineno': record.lineno,
            'process': record.process,
        }
        # Extend this formatter to handle access log specific fields if necessary
        if hasattr(record, 'request_line'):
            log_record.update({
                'client_ip': record.client_ip,
                'request_line': record.request_line,
                'status_code': record.status_code,
                'response_length': record.response_length
            })
        return json.dumps(log_record)


# Custom StreamHandler to log stdout and stderr
class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def on_starting(server):
    # Define the custom JSON formatter
    formatter = JsonFormatter()

    # Set up a handler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(LevelBasedFilter(logging.INFO))
    stdout_handler.setFormatter(formatter)

    # Set up a handler for stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)

    # Clear existing handlers and set new handlers for the Gunicorn error logger
    for handler in server.log.error_log.handlers:
        handler.close()
    server.log.error_log.handlers = [stdout_handler, stderr_handler]

    # # Apply the custom formatter to all handlers in Gunicorn's access log
    # for handler in server.log.access_log.handlers:
    #     handler.setFormatter(formatter)
    # server.log.access_log = server.log.error_log
    # # server.log.access_log.handlers = [stdout_handler, stderr_handler]

    # Set up the access log with the same handlers
    server.log.access_log.handlers = [stdout_handler, stderr_handler]

    # Add Gunicorn handlers to the root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove any default handlers
    root_logger.setLevel(logging.INFO)  # Capture all levels
    root_logger.handlers = [stdout_handler, stderr_handler]

    # Capture warnings as logs
    logging.captureWarnings(True)  # This will route warnings to the logging system
    # Ensure that captured warnings go through the same formatting
    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.handlers = [stdout_handler, stderr_handler]


