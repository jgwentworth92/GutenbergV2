from datetime import timedelta
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from icecream import ic
from confluent_kafka import OFFSET_STORED
from config.config_setting import config
from logging_config import setup_logging, get_logger
from models import constants
from services.github_service import fetch_and_emit_commits
import orjson

from services.user_management_service import user_management_service
from utils.dataflow_processing_utils import extract_job_id

setup_logging()
logger = get_logger(__name__)

# Application setup
brokers = [config.BROKERS]
input_topic = config.GITHUB_TOPIC
output_topic = config.OUTPUT_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG

# Bytewax dataflow setup
flow = Dataflow("github_commit_processing")
ic(f"the stored offset is {OFFSET_STORED}")

# Input from Kafka topic
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, topics=[input_topic],
                                   add_config=producer_config))


def update_status_in_progress(msg: KafkaSourceMessage):
    message = orjson.loads(msg.value)

    job_id = message["job_id"]
    logger.info(f"Updating status for job id {job_id}")
    user_management_service.update_status(
        job_id,
        constants.Service.DATAFLOW_TYPE_processing_raw.value,
        constants.StepStatus.IN_PROGRESS.value,
    )
    return  message


messages = op.map(
    "update_status_in_progress",
    kafka_input,
    update_status_in_progress,
)

processed_commits = op.flat_map("fetch_and_emit_commits", messages,
                                lambda msg: fetch_and_emit_commits(msg))


def update_status_complete(processed_docs):
    if processed_docs:
        job_id = processed_docs[0].metadata["job_id"]
        logger.info(f"Updating status to complete for job id {job_id}")
        user_management_service.update_status(
            job_id,
            constants.Service.DATAFLOW_TYPE_processing_raw.value,
            constants.StepStatus.COMPLETE.value,
        )
    return [doc.model_dump_json() for doc in processed_docs]


completed_messages = op.map("update_status_complete", processed_commits, update_status_complete)
kafka_messages = op.map("create_kafka_messages", completed_messages, lambda x: KafkaSinkMessage(None, orjson.dumps(x)))

# Output serialized data to Kafka
op.output("kafka-vector-raw-add", kafka_messages,
          KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config, ))
