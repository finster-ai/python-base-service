import json
from google.cloud import pubsub_v1
from concurrent.futures import ThreadPoolExecutor
from google.api_core.exceptions import NotFound, AlreadyExists

from app_instance import app, logger  # Updated import to include logger from app_instance


def consume_message(message):
    logger.info("Message received: %s", message.data)
    try:
        data = json.loads(message.data.decode('utf-8'))
        logger.info("Message deserialized successfully")
        logger.info("Message processing finished successfully")
    except Exception as e:
        logger.error(f"Error processing message: {type(e).__name__} – {e}")
    logger.info("Doing ACK to pub/sub")
    message.ack()


def create_topic_if_not_exists(publisher, topic_path):
    try:
        publisher.get_topic(topic=topic_path)
        logger.info(f"Topic {topic_path} already exists.")
    except NotFound:
        publisher.create_topic(name=topic_path)
        logger.info(f"Created topic: {topic_path}")


def create_subscription_if_not_exists(subscriber, topic_path, subscription_path):
    try:
        subscriber.get_subscription(subscription=subscription_path)
        logger.info(f"Subscription {subscription_path} already exists.")
    except NotFound:
        subscriber.create_subscription(name=subscription_path, topic=topic_path)
        logger.info(f"Created subscription: {subscription_path}")


def start_subscriber(callback, max_workers=1):
    project_id = app.config['PUBSUB_PROJECT_ID']
    topic_id = app.config['PUBSUB_TOPIC_ID']
    subscription_id = app.config['PUBSUB_SUBSCRIPTION_ID']

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    # Ensure the topic and subscription exist
    create_topic_if_not_exists(publisher, topic_path)
    create_subscription_if_not_exists(subscriber, topic_path, subscription_path)

    logger.info("Creating ThreadPoolExecutor with max_workers=%d", max_workers)
    executor = ThreadPoolExecutor(max_workers=max_workers)

    logger.info("Creating Pub/Sub subscriber client")

    logger.info(f"Subscribing to {subscription_path}")
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



