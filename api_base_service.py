

#api_base_service.py

import os
import threading
import yaml
from flask import jsonify
from flask_cors import cross_origin
from google.cloud import pubsub_v1
from concurrent.futures import ThreadPoolExecutor
from flasgger import Swagger
from app.service import AuthService
from app.service.AuthService import requires_auth, set_auth_config
from app.service.gcp_logging import logger
from app_instance import app
import logging



# Ensure Gunicorn logs go through the root logger
gunicorn_error_logger = logging.getLogger('gunicorn.error')
gunicorn_error_logger.handlers = logger.handlers
gunicorn_error_logger.setLevel(logger.level)

gunicorn_access_logger = logging.getLogger('gunicorn.access')
gunicorn_access_logger.handlers = logger.handlers
gunicorn_access_logger.setLevel(logger.level)

# Add these print statements to verify logger handlers
print(f"Root logger handlers 2: {logging.getLogger().handlers}")
print(f"Gunicorn error logger handlers 2: {gunicorn_error_logger.handlers}")
print(f"Gunicorn access logger handlers 2: {gunicorn_access_logger.handlers}")


def create_app():
    # Initialize Flask app
    # app = Flask(__name__)

    # Add a test log statement
    logger.info("TEST: Logging is set up correctly.")
    logger.info("TEST: Logging is set up correctly 2.")

    # Add Environment Values to the App
    # configure_app_environment_values(app)

    # Set auth configuration
    set_auth_config(app.config['AUTH_DOMAIN'], app.config['AUTH_AUDIENCE'], app.config['AUTH_ALGORITHMS'], app.config['DEFAULT_ENVIRONMENT'])
    # logger.info(f"Merged config: {config}\n\n\n")

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

    def start_subscriber(callback, max_workers=1):
        project_id = app.config['PUBSUB_PROJECT_ID']
        topic_id = app.config['PUBSUB_TOPIC_ID']
        subscription_id = app.config['PUBSUB_SUBSCRIPTION_ID']
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_id)
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_id)
        """
        Starts the Pub/Sub subscriber to listen for messages on a given subscription.
        Subscribes to the specified subscription path and processes messages using the
        templates_topic_call_back function. This function waits for messages to be received
        and processed.

        Args:
            callback (function): The callback function to process received messages.
            max_workers (int): The maximum number of concurrent worker threads.
        """

        # Create a custom ThreadPoolExecutor with a maximum number of workers
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

    # return app


# This is the entry point for Gunicorn
# app = create_app()
create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)




