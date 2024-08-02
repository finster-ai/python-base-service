import logging
import os
import sys
import threading
from google.cloud import logging as cloud_logging
import warnings


# Suppress all warnings
warnings.filterwarnings("ignore")

# Set Default Environment
defaultEnvironment = 'local'

# Determine the environment from an environment variable
environment = os.getenv('FLASK_ENV', defaultEnvironment)



# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the logger's level to DEBUG to capture all log levels

# Configure the root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

if environment == 'development' or environment == 'production':
    # Initialize Google Cloud Logging client and attach handler
    cloud_logger_client = cloud_logging.Client()
    # cloud_logger_client.setup_logging() - this one initializes the logger without the default handler

    # Create a custom handler for Google Cloud Logging
    cloud_handler = cloud_logger_client.get_default_handler()
    cloud_handler.setLevel(logging.INFO)

    # Create formatter and add it to the cloud handler
    formatter = logging.Formatter('[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
    cloud_handler.setFormatter(formatter)

    # Attach the custom handler to the root logger
    root_logger.addHandler(cloud_handler)

    # Optional: remove existing handlers if needed (e.g., default GCP handlers)
    for handler in root_logger.handlers:
        if not isinstance(handler, cloud_handler.__class__):
            root_logger.removeHandler(handler)

else:
    # Create console handler and set level to debug
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('[%(asctime)s +0000] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
    console_handler.setFormatter(formatter)

    # Add console handler to root logger
    root_logger.addHandler(console_handler)


# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Optionally, you can suppress other types of warnings similarly
warnings.filterwarnings("ignore", category=UserWarning)





# Adjust logging level for sentence_transformers
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)


# Redirect unhandled exceptions to the logger
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Redirected Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


# Capture threading exceptions
def log_threading_exceptions(args):
    logger.error("Exception in thread %s", args.thread.name, exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


threading.excepthook = log_threading_exceptions


# setup loguru logger and also send through GCP
# def setup_logger(
#         name: str = "data-feed",
#         level: int = logging.DEBUG,
#         project_id: str = "my_project",
#         new_logger=False
# ):
#
#     return logger
