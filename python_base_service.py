#  python_base_service.py

import threading
import logging
from app.controller.controller import router
from app.service import auth_service
from app_instance import app, logger, print_test_logs
from app.pubsub import gcp_pub_sub_consumer
from app.grpc.base_model1_grpc_impl import serve
from logging_config import setup_logging_gcp, setup_logging_local
from fastapi import HTTPException
from app.utils.api_utils import RequestStateMiddleware, custom_handle_auth_error, custom_handle_http_error, custom_handle_generic_error

# Print debug logs
print_test_logs()
logger.info(f"/n/n/n--------------------------------------------------------- APP RUNNING IN {app.state.ENVIRONMENT} ENVIRONMENT ---------------------------------------------------------/n/n/n")

app.include_router(router)
app.add_middleware(RequestStateMiddleware)

# Register the error handlers with the app
app.add_exception_handler(auth_service.AuthError, custom_handle_auth_error)
app.add_exception_handler(HTTPException, custom_handle_http_error)
app.add_exception_handler(Exception, custom_handle_generic_error)


# @app.get("/test")
# async def streaming():
#     logger.info("REACHED TEST UVICORN ENDPOINT")
#     response = "Hello from TEST UVICORN ENDPOINT"
#     return {"message": response}



# Start the Pub/Sub subscriber thread
logger.info("--------------------------------    Starting Pub/Sub subscriber thread...    --------------------------------")
logger.info("Starting the subscriber thread...")
subscriber_thread = threading.Thread(
    target=gcp_pub_sub_consumer.start_subscriber,
    args=(gcp_pub_sub_consumer.consume_message,),
    kwargs={"max_workers": 2},
    daemon=True
)
subscriber_thread.start()
logger.info("Subscriber thread started successfully.")
logger.info("------------------------------    Pub/Sub subscriber started successfully   ------------------------------")

# Start gRPC service in a separate thread
logger.info("-----------------------------------    Starting gRPC service thread...    -----------------------------------")
grpc_thread = threading.Thread(target=serve)
grpc_thread.start()
logger.info("----------------------------------   gRPC service started successfully   ----------------------------------")

# Change the log level to INFO after the startup event is complete
if app.state.ENVIRONMENT != 'local':
    setup_logging_gcp(logging.INFO)  # Setup logging before the app starts
else:
    setup_logging_local(logging.INFO)



@app.get("/test")
async def streaming():
    logger.info("REACHED TEST UVICORN ENDPOINT")
    response = "Hello from TEST UVICORN ENDPOINT"
    return {"message": response}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app_instance:app", host="0.0.0.0", port=8080)
