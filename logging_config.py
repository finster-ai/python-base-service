import logging
import sys
from uvicorn.config import LOGGING_CONFIG
import json


class HumanReadableFormatter(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        log_record = f"{self.formatTime(record, '%Y-%m-%d %H:%M:%S')} - {record.levelname} - {record.message}"
        return log_record

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



def setup_logging(min_log_level):
    # Define the human-readable formatter
    # formatter = HumanReadableFormatter()
    formatter = JsonFormatter()

    # Set up a handler for stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(min_log_level)
    stdout_handler.addFilter(LevelBasedFilter(logging.INFO))
    stdout_handler.setFormatter(formatter)

    # Set up a handler for stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)

    # Clear existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(min_log_level)  # Capture all levels
    root_logger.handlers = [stdout_handler, stderr_handler]

    # Configure Uvicorn error logger (equivalent to Gunicorn error_log)
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.handlers = []  # Clear any existing handlers
    uvicorn_error_logger.handlers.clear()
    uvicorn_error_logger.addHandler(stdout_handler)
    uvicorn_error_logger.addHandler(stderr_handler)

    # Configure Uvicorn access logger (for access logs)
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = []  # Clear any existing handlers
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(stdout_handler)
    # You can also set `stderr_handler` here if you want higher-level logs (e.g., errors) from access logs

    # Ensure Uvicorn loggers don’t propagate to the root logger, to avoid duplicate logs
    # uvicorn_error_logger.propagate = False
    # uvicorn_access_logger.propagate = False

    # Update the Uvicorn logging config dictionary
    logging_config = LOGGING_CONFIG
    logging_config['formatters']['default'] = {
        '()': JsonFormatter,
    }
    logging_config['formatters']['access'] = {
        '()': JsonFormatter,
    }
    logging.config.dictConfig(logging_config)
