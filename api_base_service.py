import os
import threading
import yaml
from flask import Flask, jsonify
from flask_cors import cross_origin
from google.cloud import pubsub_v1
from concurrent.futures import ThreadPoolExecutor
from flasgger import Swagger
from app.service import AuthService
from app.service.AuthService import requires_auth, set_auth_config
import logging

# Initialize these variables with None
defaultEnvironment = 'local'
# defaultEnvironment = 'development'
# defaultEnvironment = 'production'


# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add console handler to logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Ensure we don't add the handler multiple times
if not logger.hasHandlers():
    logger.addHandler(console_handler)


def deep_merge_dicts(a, b):
    """Deep merge two dictionaries."""
    result = a.copy()
    for key, value in b.items():
        if isinstance(value, dict) and key in result:
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def configure_app_environment_values(app):
    # Determine the environment from an environment variable
    environment = os.getenv('FLASK_ENV', defaultEnvironment)

    # Set the environment in the app config
    app.config['ENVIRONMENT'] = environment

    # Load the common configuration file
    with open('config/common.yaml', 'r') as common_file:
        common_config = yaml.safe_load(common_file)

    # Load the environment-specific configuration file
    config_file = f'config/config_{environment}.yaml'
    with open(config_file, 'r') as env_file:
        env_config = yaml.safe_load(env_file)

    # Deep merge configurations, with environment-specific settings overriding common settings
    config = deep_merge_dicts(common_config, env_config)
    logger.info(f"Merged config: {config}")

    # Update Flask configuration
    for key, value in config.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                app.config[f"{key.upper()}_{sub_key.upper()}"] = sub_value
        else:
            app.config[key.upper()] = value
    # app.config.update(
    #     ENVIRONMENT=environment,
    #     SECRET_KEY=config['app']['secret_key'],
    #     DEBUG=config['app']['debug'],
    #     VERSION=config['app']['version'],
    #     SQLALCHEMY_DATABASE_URI=config['database']['uri'],
    #     SQLALCHEMY_POOL_SIZE=config['database']['pool_size'],
    #     AUTH0_DOMAIN=config['auth']['domain'],
    #     API_AUDIENCE=config['auth']['audience'],
    #     ALGORITHMS=config['auth']['algorithms'],
    # )


def configure_pub_sub_queues(app):
    # Google Pub/Sub configuration
    project_id = app.config['PUBSUB_PROJECT_ID']
    topic_id = app.config['PUBSUB_TOPIC_ID']
    subscription_id = app.config['PUBSUB_SUBSCRIPTION_ID']
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)


def create_app():
    # Initialize Flask app
    app = Flask(__name__)

    # Add a test log statement
    logger.info("TEST: Logging is set up correctly.")
    logger.info("TEST: Logging is set up correctly 2.")

    # Add Environment Values to the App
    configure_app_environment_values(app)

    # Set auth configuration
    set_auth_config(app.config['AUTH_DOMAIN'], app.config['AUTH_AUDIENCE'], app.config['AUTH_ALGORITHMS'])
    # logger.info(f"Merged config: {config}\n\n\n")

    # Google Pub/Sub configuration
    configure_pub_sub_queues(app)

    # Log the running environment, database URL, and topic ID
    logger.info("\n\n\n\n###################################################################################################################################################################################################################################")
    logger.info(f"RUNNING ENVIRONMENT: {app.config['ENVIRONMENT']}\n")
    # logger.info(f"Database URL: {app.config['DATABASE_SQL_URI']}")
    logger.info(f"Pub/Sub Topic ID: {app.config['PUBSUB_TOPIC_ID']}")
    logger.info(f"Auth Domain: {app.config['AUTH_DOMAIN']}")
    logger.info(f"API Audience: {app.config['AUTH_AUDIENCE']}")
    logger.info(f"MongoDB URI: {app.config['DATABASE_MONGODB']['uri']}\n###################################################################################################################################################################################################################################\n\n\n")

    # Construct the correct path to the YAML file
    current_dir = os.path.dirname(__file__)
    yaml_file_path = os.path.join(current_dir, 'app', 'utils', 'swagger_docs.yaml')

    # Print the path to ensure it's correct
    logger.info(f"YAML file path: {yaml_file_path}")

    # Load the Swagger configuration from the YAML file
    with open(yaml_file_path, 'r') as file:
        swagger_template = yaml.safe_load(file)
    swagger = Swagger(app, template=swagger_template)

    def templates_topic_call_back(message):
        logger.info("Message received: %s", message.data)
        logger.info("Message processing finished")
        message.ack()

    def start_subscriber(callback, subscription_path, max_workers=1):
        logger.info("Creating ThreadPoolExecutor with max_workers=%d", max_workers)
        executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info("Creating Pub/Sub subscriber client")
        subscriber = pubsub_v1.SubscriberClient()
        logger.info("Subscribing to %s", subscription_path)
        try:
            streaming_pull_future = subscriber.subscribe(
                subscription_path,
                callback=callback,
                scheduler=pubsub_v1.subscriber.scheduler.ThreadScheduler(executor=executor)
            )
            logger.info(f"Listening for messages on {subscription_path}..\n")
            with subscriber:
                try:
                    streaming_pull_future.result()
                except TimeoutError:
                    logger.error("TimeoutError encountered, cancelling streaming_pull_future..")
                    streaming_pull_future.cancel()
                except Exception as e:
                    logger.error("An error occurred in the subscriber: %s", e)
                    streaming_pull_future.cancel()
        except Exception as e:
            logger.error("Failed to start subscriber: %s", e)

    @app.errorhandler(AuthService.AuthError)
    def handle_auth_error(ex):
        response = jsonify(ex.error)
        response.status_code = ex.status_code
        return response

    # This doesn't need authentication
    @app.route("/api/public")
    @cross_origin(headers=["Content-Type", "Authorization"])
    def public():
        response = jsonify(":A:A:A:A")
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("ContentType", "application/json")
        logger.info("Listening for messages you've reached this endpoint")
        return response

    # This needs authentication
    @app.route("/api/private")
    @cross_origin(headers=["Content-Type", "Authorization"])
    @requires_auth
    def private():
        response = (
            "Hello from a private endpoint! You need to be authenticated to see this."
        )
        return jsonify(message=response)

    @app.route("/")
    def hello_world():  # put application's code here
        return "Hello World!"

    logger.info("Starting the app")
    try:
        logger.info("Starting the subscriber thread...")
        subscriber_thread = threading.Thread(target=start_subscriber,
                                             args=(templates_topic_call_back,),
                                             kwargs={"max_workers": 1},
                                             daemon=True)
        subscriber_thread.start()
        logger.info("Subscriber thread started successfully.")
    except Exception as e:
        logger.error(f"Failed to start subscriber thread: {e}")

    return app


# This is the entry point for Gunicorn
app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
