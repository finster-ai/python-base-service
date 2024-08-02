# app_instance.py

from flask import Flask
from flask_cors import CORS
import re
import os
import yaml
# import logging
from app.service.gcp_logging import logger



app = Flask(__name__)
CORS(app, supports_credentials=True)

# Set Default Environment
defaultEnvironment = 'local'
# defaultEnvironment = 'development'
# defaultEnvironment = 'production'


def deep_merge_dicts(a, b):
    """Deep merge two dictionaries."""
    result = a.copy()
    for key, value in b.items():
        if isinstance(value, dict) and key in result:
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def print_test_logs():
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")


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
    logger.info(f"MongoDB URI: {replace_sensitive_info(app.config['DATABASE_MONGODB_URI'])}\n###################################################################################################################################################################################################################################\n\n\n")


def configure_app_environment_values():
    """
    Configures environment values for the app
    """

    # Determine the environment from an environment variable
    environment = os.getenv('FLASK_ENV', defaultEnvironment)

    # Set the environment in the app config
    app.config['ENVIRONMENT'] = environment

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
