# app_instance.py

import logging  # Add this line
import os
import re
import yaml

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.custom_logger import CustomLogger, ContextualFilter
from logging_config import setup_logging_gcp, setup_logging_local



# Set the default logging level
LOG_LEVEL = logging.DEBUG

# Set Default Environment - local, development, production
defaultEnvironment = 'local'

defaultProjectId = 'daring-keep-408013'
defaultLocation = 'us-central1'
environment = os.getenv('FLASK_ENV', defaultEnvironment)




# Set the custom logger class before any logger is created
# logging.setLoggerClass(CustomLogger)

# Call setup_logging before defining logger
if environment != 'local':
    setup_logging_gcp(LOG_LEVEL)  # Setup logging before the app starts
else:
    setup_logging_local(LOG_LEVEL)
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


# Apply filter to third-party loggers
third_party_loggers = ['urllib3', 'requests', '_client', 'httpx']
contextual_filter = ContextualFilter()
for logger_name in third_party_loggers:
    third_party_logger = logging.getLogger(logger_name)
    third_party_logger.setLevel(logging.INFO)
    third_party_logger.addFilter(contextual_filter)


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





# Configures environment values for the app
def configure_app_environment_values():
    logger.info("Configuring environment values")


    # Set environment values using app.state
    app.state.ENVIRONMENT = environment
    app.state.APP_PROJECT_ID = os.getenv('PROJECT_ID', defaultProjectId)
    app.state.APP_LOCATION = os.getenv('LOCATION', defaultLocation)
    app.state.DEFAULT_ENVIRONMENT = defaultEnvironment


    # Load the common configuration file
    with open('config/common.yaml', 'r') as common_file:
        common_config = yaml.safe_load(common_file)

    # Load the environment-specific configuration file
    config_file = f'config/config_{environment}.yaml'
    with open(config_file, 'r') as env_file:
        env_config = yaml.safe_load(env_file)

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



def print_test_logs():
    logger.debug("This is a DEBUG message.")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.critical("This is a CRITICAL message.")




configure_app_environment_values()
# TODO: move to gcp secrets.
# redis_client = redis.Redis(
#     host=app.state.DATABASE_REDIS_HOST,
#     port=app.state.DATABASE_REDIS_PORT,
#     password=app.state.DATABASE_REDIS_PASSWORD,
# )

# Initialize Cohere client with your API key
# co = cohere.Client(app.state.COHERE_API_KEY)  # This is your trial API key

# Initialize PostHog client with your project API key
# posthog.project_api_key = app.state.POSTHOG_PROJECT_API_KEY


# print("This is stdout", file=sys.stdout)
# print("This is stderr", file=sys.stderr)






# def replace_sensitive_info(line):
#     # Define the allowed set and the exception words
#     allowed_set = r'[^./-]'
#     exception_words = ['finster', 'FINSTER', 'dev', 'DEV', 'mongodb', 'http', 'https', 'com', 'org', 'net']
#
#     # Create a regex pattern for the exception words
#     exception_pattern = r'|'.join(map(re.escape, exception_words))
#
#     # Split the line into segments that are exception words or everything else
#     segments = re.split(f'({exception_pattern})', line, flags=re.IGNORECASE)
#
#     # Process each segment
#     sanitized_segments = []
#     for segment in segments:
#         if segment.lower() in [word.lower() for word in exception_words]:
#             sanitized_segments.append(segment)  # Preserve the exception words
#         else:
#             # Replace characters not in the allowed set with asterisks
#             sanitized_segments.append(re.sub(allowed_set, '*', segment))
#
#     # Rejoin the processed segments
#     sanitized_part = ''.join(sanitized_segments)
#     return sanitized_part
