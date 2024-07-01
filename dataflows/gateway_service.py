import orjson
from config.config_setting import config
from bytewax import operators as op
from bytewax.connectors.kafka import (
    KafkaSource,
    KafkaSink,
    KafkaSinkMessage,
    KafkaSourceMessage,
)
from bytewax.dataflow import Dataflow
from models import constants
from services.user_management_service import user_management_service
from logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

flow = Dataflow("Gateway Service")

RESOURCE_TOPIC_MAPPING = {"github": config.GITHUB_TOPIC, "pdf": config.PDF_INPUT}

kafka_input = op.input(
    "read-kafka-message",
    flow,
    KafkaSource(
        brokers=[config.BROKERS],
        topics=[config.RESOURCE_TOPIC],
        add_config=config.CONSUMER_CONFIG,
    ),
)


def process_message(msg: KafkaSourceMessage):
    data = orjson.loads(msg.value)
    row = data["payload"]["after"]
    resource_type = row["resource_type"]
    job_id = row["job_id"]
    logger.info(
        f"data type submitted to gateway dataflow {resource_type} with payload: {row}"
    )

    if resource_type in RESOURCE_TOPIC_MAPPING:
        user_management_service.update_status(
            constants.Service.GATEWAY_SERVICE,
            job_id,
            constants.StepStatus.COMPLETE.value,
        )
        logger.error(f"Updated the status")
        return KafkaSinkMessage(
            None, orjson.dumps(row), topic=RESOURCE_TOPIC_MAPPING[resource_type]
        )
    else:
        logger.error(f"Unrecognised resource! {resource_type}")
        user_management_service.update_status(
            constants.Service.GATEWAY_SERVICE, job_id, constants.StepStatus.COMPLETE
        )
        return None


def update_status_in_progress(msg: KafkaSourceMessage):
    data = orjson.loads(msg.value)
    row = data["payload"]["after"]

    job_id = row["job_id"]
    logger.info(f"Updating status for job id {job_id}")
    user_management_service.update_status(
        constants.Service.GATEWAY_SERVICE,
        job_id,
        constants.StepStatus.IN_PROGRESS.value,
    )
    return msg


messages = op.map(
    "update_status_in_progress",
    kafka_input,
    update_status_in_progress,
)

processed_messages = op.map(
    "process_message",
    messages,
    process_message,
)

# Filter out None values
valid_messages = op.filter(
    "filter_valid_messages",
    processed_messages,
    lambda msg: msg is not None,
)

op.output(
    "kafka-output", valid_messages, KafkaSink(brokers=[config.BROKERS], topic=None)
)
