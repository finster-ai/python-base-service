#api_base_service.py
import os
import yaml
from flasgger import Swagger

from app.grpc.base_model1_grpc_impl import serve
from app_instance import app, logger  # Updated import to include logger from app_instance
from app.controller.controller import controller_blueprint, url_prefix_controller
import threading
from app_instance import app
from app.pubsub import gcp_pub_sub_consumer
# from app.grpc_server import start_grpc_server

os.environ['GRPC_VERBOSITY'] = 'ERROR'


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

    try:
        logger.info("Starting the subscriber thread...")
        subscriber_thread = threading.Thread(target=gcp_pub_sub_consumer.start_subscriber,
                                             args=(gcp_pub_sub_consumer.consume_message,),
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




