# logging_config.py

import logging
import os
import sys
from uvicorn.config import LOGGING_CONFIG
import json
import time
import traceback


class HumanReadableFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Correct format with milliseconds and timezone
        ct = self.converter(record.created)
        t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        s = f"{t},{int(record.msecs):03d} {time.strftime('%z', ct)}"
        return s

    def format(self, record):
        # Format the timestamp with milliseconds and timezone
        timestamp = self.formatTime(record)

        # Get the process ID
        process_id = os.getpid()

        # Get the file name and line number
        filename = record.pathname.split(os.sep)[-1]
        lineno = record.lineno

        # Ensure the log message is generated correctly with any arguments provided
        message = record.getMessage()

        # Construct the log message
        log_record = (
            f"[{timestamp}] [{process_id}] [{record.levelname}] "
            f"[{filename}:{lineno}] {message}"
        )

        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            exception_type_text = f"{exc_type.__name__}: "
            exception_value_text = f"{str(exc_value)}"
            exception_text = ''.join(traceback.format_tb(exc_traceback)) + exception_type_text + exception_value_text
            # exception_text = self.formatException(record.exc_info)
            log_record += f"\nStack trace:\n{exception_text}"
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
        # If there is an exception, add the stack trace to the log record
        # if record.exc_info:
        #     # Format the exception information (stack trace)
        #     exception_text = self.formatException(record.exc_info)
        #     log_record['stack_trace'] = exception_text
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            exception_type_text = f"{exc_type.__name__}: "
            exception_value_text = f"{str(exc_value)}"
            exception_text = ''.join(traceback.format_tb(exc_traceback)) + exception_type_text + exception_value_text
            # exception_text = self.formatException(record.exc_info)
            log_record['stack_trace'] = f"\nStack trace:\n{exception_text}"

        # Extend this formatter to handle access log specific fields if necessary
        if hasattr(record, 'request_line'):
            log_record.update({
                'client_ip': record.client_ip,
                'request_line': record.request_line,
                'status_code': record.status_code,
                'response_length': record.response_length
            })
        return json.dumps(log_record)



def setup_logging_gcp(min_log_level):
    # Define the  JSON formatter for GCP
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


    # Update the Uvicorn logging config dictionary
    logging_config = LOGGING_CONFIG
    logging_config['formatters']['default'] = {
        '()': JsonFormatter,
    }
    logging_config['formatters']['access'] = {
        '()': JsonFormatter,
    }
    logging.config.dictConfig(logging_config)



def setup_logging_local(min_log_level):
    formatter = HumanReadableFormatter()

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


    #  TODO: ESTO NO FUNCIONO PARA DESHACERME DE ESTOS LOGS [2024-09-17 19:20:19,264 +0100] [67874] [INFO] [h11_impl.py:476] 127.0.0.1:57426 - "GET /api/v2/history/emmanuel%40finster.ai HTTP/1.1" 200
    # # Get Uvicorn loggers
    # uvicorn_logger = logging.getLogger("uvicorn")
    # uvicorn_error_logger = logging.getLogger("uvicorn.error")
    # uvicorn_access_logger = logging.getLogger("uvicorn.access")
    #
    # # If min_log_level is 'info', set loggers to 'warning', otherwise set them to min_log_level
    # if min_log_level == logging.INFO:
    #     uvicorn_logger.setLevel(logging.WARNING)
    #     uvicorn_error_logger.setLevel(logging.WARNING)
    #     uvicorn_access_logger.setLevel(logging.WARNING)
    # else:
    #     uvicorn_logger.setLevel(min_log_level)
    #     uvicorn_error_logger.setLevel(min_log_level)
    #     uvicorn_access_logger.setLevel(min_log_level)
    #  TODO: ESTO NO FUNCIONO PARA DESHACERME DE ESTOS LOGS [2024-09-17 19:20:19,264 +0100] [67874] [INFO] [h11_impl.py:476] 127.0.0.1:57426 - "GET /api/v2/history/emmanuel%40finster.ai HTTP/1.1" 200




    logging_config = LOGGING_CONFIG

    # Add custom handlers to the logging config
    logging_config['handlers']['custom_stdout'] = {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default',  # Use the 'default' formatter - The handlers now refer to the 'default' formatter, which is configured to use the HumanReadableFormatter.
        'level': 'INFO'
    }

    logging_config['handlers']['custom_stderr'] = {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stderr',
        'formatter': 'default',  # Use the 'default' formatter - The handlers now refer to the 'default' formatter, which is configured to use the HumanReadableFormatter.
        'level': 'WARNING'
    }

    # Update loggers to use the new custom handlers
    logging_config['loggers']['uvicorn']['handlers'] = ['custom_stdout', 'custom_stderr']
    logging_config['loggers']['uvicorn.access']['handlers'] = ['custom_stdout']
    logging_config['loggers']['uvicorn.error']['handlers'] = ['custom_stderr']




    logging_config['formatters']['default'] = {
        '()': HumanReadableFormatter,
    }
    logging_config['formatters']['access'] = {
        '()': HumanReadableFormatter,
    }


    logging.config.dictConfig(logging_config)
