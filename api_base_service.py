
#api_base_service.py
import os
import threading
import yaml
from google.cloud import pubsub_v1
from concurrent.futures import ThreadPoolExecutor
from flasgger import Swagger

from app.grpc.base_model1_grpc_impl import serve
from app.utils.wrappers import set_session_id, query_tracking_with_id
from app_instance import app, logger  # Updated import to include logger from app_instance
from app.controller.controller import controller_blueprint, url_prefix_controller
import threading
from app_instance import app
from multiprocessing import Process
# from app.grpc_server import start_grpc_server


def create_app():
    # Register blueprints
    app.register_blueprint(controller_blueprint, url_prefix=url_prefix_controller)

    # Add a test log statement
    logger.info("TEST: Logging is set up correctly.")

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

    # grpc_process = Process(target=serve)
    # grpc_process.start()


# This is the entry point for Gunicorn
create_app()
# Start the GRPC server before running the Flask app
grpc_thread = threading.Thread(target=serve)
grpc_thread.start()

if __name__ == "__main__":
    # grpc_process = Process(target=serve)
    # grpc_process.start()
    app.run(host="0.0.0.0", port=8080, debug=False)




