# app_instance.py
import re
import os
import yaml
import logging
from flask import Flask, g, has_request_context
from flask_cors import CORS

# Set the default logging level
# LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Set Default Environment
defaultEnvironment = 'local'
# defaultEnvironment = 'development'
# defaultEnvironment = 'production'
defaultProjectId = 'daring-keep-408013'
defaultLocation = 'us-central1'


class CustomLogger(logging.getLoggerClass()):
    def build_msg(self, msg):
        if has_request_context():
            request_id = getattr(g, 'request_id', '')
            session_id = getattr(g, 'session_id', '')
            user_id = getattr(g, 'user_id', '')
            query_id = getattr(g, 'query_id', '')
            parts = []
            if request_id:
                parts.append(f"[request_id: {request_id}]")
            if session_id:
                parts.append(f"[session_id: {session_id}]")
            if user_id:
                parts.append(f"[user_id: {user_id}]")
            if query_id:
                parts.append(f"[query_id: {query_id}]")

            prefix = " ".join(parts)
            return f"{prefix} {msg}" if prefix else msg
        else:
            return msg

    def info(self, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        super().info(msg, *args, stacklevel=2, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        super().warning(msg, *args, stacklevel=2, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        super().error(msg, *args, stacklevel=2, **kwargs)

    def debug(self, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        super().debug(msg, *args, stacklevel=2, **kwargs)

    def critical(self, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        super().critical(msg, *args, stacklevel=2, **kwargs)

    def exception(self, msg, *args, **kwargs):
        msg = self.build_msg(msg)
        super().exception(msg, *args, stacklevel=2, **kwargs)


# Set the custom logger class before any logger is created
logging.setLoggerClass(CustomLogger)

# Configure logging to work with Gunicorn or in standalone mode
gunicorn_logger = logging.getLogger('gunicorn.error')

if gunicorn_logger.handlers:
    # If Gunicorn is available, use its handlers
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(LOG_LEVEL)
    app.logger.info("USING GUNICORN HANDLERS")
else:
    # Otherwise, set up a new handler for the root logger
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'))
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Clear existing handlers
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)
    root_logger.propagate = False
    app.logger.handlers = [handler]
    app.logger.setLevel(LOG_LEVEL)
    app.logger.info("USING NEW SET UP HANDLERS")


# Ensure no log messages are duplicated
app.logger.propagate = False
# Set a global `logger` to `app.logger` to use throughout the module
logger = app.logger


def set_tracking_prefix(prefix=None):
    global tracking_prefix
    tracking_prefix = prefix if prefix else ""
    app.logger.info(f"Tracking prefix set to: {tracking_prefix}")


def print_test_logs():
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")


def deep_merge_dicts(a, b):
    """Deep merge two dictionaries."""
    result = a.copy()
    for key, value in b.items():
        if isinstance(value, dict) and key in result:
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def rename_keys(d, parent_key=''):
    # Renames the keys of a dictionary in the format 'parentKey_childKey'.
    items = {}
    for key, value in d.items():
        new_key = f"{parent_key}_{key}".strip('_')
        if isinstance(value, dict):
            nested_items = rename_keys(value, new_key)
            items.update(nested_items)
        else:
            items[new_key] = value
    return items


def replace_sensitive_info(line):
    # Define the allowed set and the exception words
    allowed_set = r'[^./-]'
    exception_words = ['finster', 'FINSTER', 'dev', 'DEV', 'mongodb', 'http', 'https', 'com', 'org', 'net']

    # Create a regex pattern for the exception words
    exception_pattern = r'|'.join(map(re.escape, exception_words))

    # Split the line into segments that are exception words or everything else
    segments = re.split(f'({exception_pattern})', line, flags=re.IGNORECASE)

    # Process each segment
    sanitized_segments = []
    for segment in segments:
        if segment.lower() in [word.lower() for word in exception_words]:
            sanitized_segments.append(segment)  # Preserve the exception words
        else:
            # Replace characters not in the allowed set with asterisks
            sanitized_segments.append(re.sub(allowed_set, '*', segment))

    # Rejoin the processed segments
    sanitized_part = ''.join(sanitized_segments)
    return sanitized_part


def print_environment_debug_logs():
    # Log the running environment, database URL, and topic ID
    if gunicorn_logger.handlers:
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("###################################################################################################################################################################################################################################")
    else:
        logger.info("\n\n\n\n###################################################################################################################################################################################################################################")

    logger.info(f"RUNNING ENVIRONMENT: {app.config['ENVIRONMENT']}\n")
    # logger.info(f"Database URL: {app.config['DATABASE_SQL_URI']}")
    logger.info(f"Pub/Sub Topic ID: {app.config['PUBSUB_TOPIC_ID']}")
    # logger.info(f"Auth Domain: {app.config['AUTH_DOMAIN']}")
    logger.info(f"Auth Domain: {replace_sensitive_info(app.config['AUTH_DOMAIN'])}")
    # logger.info(f"API Audience: {app.config['AUTH_AUDIENCE']}")
    logger.info(f"API Audience: {replace_sensitive_info(app.config['AUTH_AUDIENCE'])}")
    logger.info(f"Project: {app.config['APP_PROJECT_ID']}")
    logger.info(f"Location: {app.config['APP_LOCATION']}")
    # logger.info(f"MongoDB URI: {app.config['DATABASE_MONGODB_URI']}")
    if gunicorn_logger.handlers:
        logger.info(f"MongoDB URI: {replace_sensitive_info(app.config['DATABASE_MONGODB_URI'])}")
        logger.info("###################################################################################################################################################################################################################################")
        logger.info("")
        logger.info("")
        logger.info("")
    else:
        logger.info(f"MongoDB URI: {replace_sensitive_info(app.config['DATABASE_MONGODB_URI'])}\n###################################################################################################################################################################################################################################\n\n\n")




def configure_app_environment_values():
    """
    Configures environment values for the app
    """

    # Determine the environment from an environment variable
    environment = os.getenv('FLASK_ENV', defaultEnvironment)

    # Set the environment in the app config
    app.config['ENVIRONMENT'] = environment

    app.config['APP_PROJECT_ID'] = os.getenv('PROJECT_ID', defaultProjectId)
    app.config['APP_LOCATION'] = os.getenv('LOCATION', defaultLocation)

    # Set the default environment in the app config
    app.config['DEFAULT_ENVIRONMENT'] = defaultEnvironment

    # Load the common configuration file
    with open('config/common.yaml', 'r') as common_file:
        common_config = yaml.safe_load(common_file)

    # Load the environment-specific configuration file
    config_file = f'config/config_{environment}.yaml'
    with open(config_file, 'r') as env_file:
        env_config = yaml.safe_load(env_file)

    # Deep merge configurations, with environment-specific settings overriding common settings
    config = deep_merge_dicts(common_config, env_config)
    # Rename the keys of the merged dictionary
    config = rename_keys(config)

    # Update Flask configuration
    for key, value in config.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                app.config[f"{key.upper()}_{sub_key.upper()}"] = sub_value
        else:
            app.config[key.upper()] = value


configure_app_environment_values()
print_environment_debug_logs()
print_test_logs()
# print_test_logs2()
