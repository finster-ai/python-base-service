# controller_pubsub_producer.py

import json

from app_instance import logger, app
from fastapi.responses import JSONResponse
from google.cloud import pubsub_v1



project_id = app.state.PUBSUB_PROJECT_ID
topic_id = app.state.PUBSUB_TOPIC_ID
subscription_id = app.state.PUBSUB_SUBSCRIPTION_ID
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)


class Message:
    user_id: str
    data_dictionary: dict
    agent_flag: str


async def template(message: Message):
    try:

        # Convert the entire request JSON to a string
        message = json.dumps(message).encode('utf-8')

        future = publisher.publish(topic_path, message)
        message_id = future.result()

        logger.info("Message published for template processing Pub/Sub Queue")
        return JSONResponse(content={'message_id': message_id}, status_code=200)

    except Exception as e:
        logger.exception(f"Error sending message into Pub/Sub queue: {str(e)}")






