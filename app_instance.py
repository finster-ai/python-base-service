# app_instance.py

import logging  # Add this line
import os
import re


import yaml

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.custom_logger import CustomLogger
from logging_config import setup_logging, setup_logging_local

# Set Default Environment
defaultEnvironment = 'local'
defaultProjectId = 'daring-keep-408013'
defaultLocation = 'us-central1'
environment = os.getenv('FLASK_ENV', defaultEnvironment)




# Set the custom logger class before any logger is created
logging.setLoggerClass(CustomLogger)

# Call setup_logging before defining logger
if environment != 'local':
    setup_logging(logging.DEBUG)  # Setup logging before the app starts
else:
    setup_logging_local(logging.DEBUG)
logger = logging.getLogger(__name__)  # Add this line to get the logger





# logger.error("APP_INSTANCE INTIALIZATION")
app = FastAPI()


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# logger.error("APP_INSTANCE INTIALIZATION - POST FATSAPI 2")

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


# Configures environment values for the app
def configure_app_environment_values():
    logger.info("Configuring environment values")
    # Determine the environment from an environment variable


    # Set environment values using app.state
    app.state.ENVIRONMENT = environment
    app.state.APP_PROJECT_ID = os.getenv('PROJECT_ID', defaultProjectId)
    app.state.APP_LOCATION = os.getenv('LOCATION', defaultLocation)
    app.state.DEFAULT_ENVIRONMENT = defaultEnvironment
    app.state.TYPE = os.getenv('TYPE', 'API')

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

    # Update FastAPI state
    for key, value in config.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                setattr(app.state, f"{key.upper()}_{sub_key.upper()}", sub_value)
        else:
            setattr(app.state, key.upper(), value)

    # Initialize PostHog client with your project API key
    # posthog.project_api_key = app.state['POSTHOG_PROJECT_API_KEY']



def print_test_logs():
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")

def print_environment_debug_logs():
    logger.info("")
    logger.info("")
    logger.info("")
    logger.info("")
    logger.info("###################################################################################################################################################################################################################################")
    logger.info(f"RUNNING ENVIRONMENT: {app.state.ENVIRONMENT}\n")
    # logger.info(f"Database URL: {app.state.DATABASE_SQL_URI}")
    logger.info(f"Pub/Sub Topic ID: {app.state.PUBSUB_TOPIC_ID}")
    # logger.info(f"Auth Domain: {replace_sensitive_info(app.state.AUTH_DOMAIN)}")
    logger.info(f"Auth Domain: {replace_sensitive_info(app.state.AUTH_DOMAIN)}")
    # logger.info(f"API Audience: {replace_sensitive_info(app.state.AUTH_AUDIENCE)}")
    logger.info(f"API Audience: {replace_sensitive_info(app.state.AUTH_AUDIENCE)}")
    logger.info(f"Project: {app.state.APP_PROJECT_ID}")
    logger.info(f"Location: {app.state.APP_LOCATION}")
    # logger.info(f"MongoDB URI: {replace_sensitive_info(app.state.DATABASE_MONGODB_URI)}")

    logger.info(f"MongoDB URI: {replace_sensitive_info(app.state.DATABASE_MONGODB_URI)}")
    logger.info("###################################################################################################################################################################################################################################")
    logger.info("")
    logger.info("")
    logger.info("")
