from typing import Optional

from bytewax.connectors.kafka import KafkaSinkMessage, KafkaSourceMessage
from orjson import orjson

from logging_config import get_logger, config
from models import constants
from utils.status_update import status_updater, StandardizedMessage

logger = get_logger(__name__)

RESOURCE_TOPIC_MAPPING = {"github": config.GITHUB_TOPIC, "pdf": config.PDF_INPUT}


def kafka_to_standardized(msg: KafkaSourceMessage) -> StandardizedMessage:
    data = orjson.loads(msg.value)
    row = data["payload"]["after"]
    return StandardizedMessage(
        job_id=row["job_id"],
        step_number=1,
        data=row,
        metadata={"original_topic": msg.topic}
    )


@status_updater(constants.Service.GATEWAY_SERVICE)
def process_and_route_message(message: StandardizedMessage) -> Optional[StandardizedMessage]:
    resource_type = message.data["resource_type"]
    logger.info(f"Processing message for job {message.job_id}, resource type: {resource_type}")

    if resource_type in RESOURCE_TOPIC_MAPPING:
        logger.info(f"Message processed successfully for job {message.job_id}")
        message.metadata["output_topic"] = RESOURCE_TOPIC_MAPPING[resource_type]
        return message
    else:
        logger.error(f"Unrecognised resource type {resource_type} for job {message.job_id}")
        return None


def standardized_to_kafka(message: Optional[StandardizedMessage]) -> Optional[KafkaSinkMessage]:
    if isinstance(message, StandardizedMessage) and "output_topic" in message.metadata:
        return KafkaSinkMessage(
            None,
            orjson.dumps(message.__dict__),
            topic=message.metadata["output_topic"]
        )
    logger.warning(f"Received invalid message or message without output_topic: {message}")
    return None
