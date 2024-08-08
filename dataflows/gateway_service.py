import orjson
from typing import Optional
from bytewax import operators as op
from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import (
    KafkaSource,
    KafkaSink,
    KafkaSinkMessage,
    KafkaSourceMessage,
)
from models import constants
from config.config_setting import config
from logging_config import get_logger, setup_logging
from utils.status_update import create_status_updater, StandardizedMessage

setup_logging()
logger = get_logger(__name__)

flow = Dataflow("Gateway Service")

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
    if message is not None and "output_topic" in message.metadata:
        return KafkaSinkMessage(
            None,
            orjson.dumps(message.__dict__),
            topic=message.metadata["output_topic"]
        )
    return None


# Create status updater
status_updater = create_status_updater(constants.Service.GATEWAY_SERVICE)

# Create processor with status updates
processor_with_status = status_updater(process_and_route_message)

# Define the dataflow
kafka_input = op.input(
    "read-kafka-message",
    flow,
    KafkaSource(
        brokers=[config.BROKERS],
        topics=[config.RESOURCE_TOPIC],
        add_config=config.CONSUMER_CONFIG,
    ),
)

standardized_messages = op.map("kafka_to_standardized", kafka_input, kafka_to_standardized)
processed_messages = op.map("process_and_route_messages", standardized_messages, processor_with_status)
kafka_messages = op.map("standardized_to_kafka", processed_messages, standardized_to_kafka)

# Filter out None values
valid_messages = op.filter("filter_valid_messages", kafka_messages, lambda msg: msg is not None)

op.output("kafka-output", valid_messages, KafkaSink(brokers=[config.BROKERS], topic=None))

logger.info("Gateway Service dataflow setup completed")
