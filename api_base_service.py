from contextlib import asynccontextmanager

from fastapi import FastAPI

import app_instance
from app_instance import app, logger, configure_app_environment_values, print_environment_debug_logs, print_test_logs
import threading
from app.pubsub import gcp_pub_sub_consumer
from app.grpc.base_model1_grpc_impl import serve
import logging

from logging_config import setup_logging, setup_logging_local

logger.error("STARTUP TAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASK")
logger.error("STARTUP TAAAAAAAAAAAAASK")
logger.error("STARTUP TAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAASK")
logger.error("STARTUP TAAAAAAAAAAAAASK")
# Configure the app environment values and print debug logs
configure_app_environment_values()
print_environment_debug_logs()
print_test_logs()

# # Start the Pub/Sub subscriber thread
# logger.info("Starting the subscriber thread...")
# subscriber_thread = threading.Thread(
#     target=gcp_pub_sub_consumer.start_subscriber,
#     args=(gcp_pub_sub_consumer.consume_message,),
#     kwargs={"max_workers": 2},
#     daemon=True
# )
# subscriber_thread.start()
# logger.info("Subscriber thread started successfully.")
#
# # Start gRPC service in a separate thread
# logger.info("Starting gRPC service thread...")
# grpc_thread = threading.Thread(target=serve)
# grpc_thread.start()
# logger.info("gRPC service started successfully.")

# Change the log level to INFO after the startup event is complete
if app.state.ENVIRONMENT != 'local':
    setup_logging(logging.INFO)  # Setup logging before the app starts
else:
    setup_logging_local(logging.INFO)



@app.get("/test")
async def streaming():
    logger.info("REACHED TEST UVICORN ENDPOINT")
    response = "Hello from TEST UVICORN ENDPOINT"
    return {"message": response}


if __name__ == "__main__":
    import uvicorn
    logger.error("ARRANCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    uvicorn.run("api_base_service:app", host="0.0.0.0", port=8080, log_level="info")
    logger.error("ARRANCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA 2")
