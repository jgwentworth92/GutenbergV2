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
def process_and_route_message(message: StandardizedMessage) -> Optional[KafkaSinkMessage]:
    resource_type = message.data["resource_type"]
    logger.info(f"Processing message for job {message.job_id}, resource type: {resource_type}")

    if resource_type in RESOURCE_TOPIC_MAPPING:
        logger.info(f"Message processed successfully for job {message.job_id}")
        output_topic = RESOURCE_TOPIC_MAPPING[resource_type]
        return KafkaSinkMessage(
            key=None,
            value=message.model_dump_json(),
            topic=output_topic
        )
    else:
        logger.error(f"Unrecognised resource type {resource_type} for job {message.job_id}")
        return None


