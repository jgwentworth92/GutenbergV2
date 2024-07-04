from datetime import timedelta
from pprint import pprint
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import (
    KafkaSource,
    KafkaSink,
    KafkaSinkMessage,
    KafkaSourceMessage,
)
from icecream import ic
from confluent_kafka import OFFSET_STORED
from config.config_setting import config
from models import constants
from logging_config import setup_logging, get_logger
from services.github_service import fetch_and_emit_commits
from services.user_management_service import user_management_service
import orjson

from utils.dataflow_processing_utils import  extract_job_id

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

def update_status_in_progress(msg: KafkaSourceMessage):
    data = orjson.loads(msg.value)
    job_id = data["job_id"]
    logger.info(f"Updating status for job id {job_id}")
    user_management_service.update_status(
        constants.Service.GITHUB_SERVICE,
        job_id,
        constants.StepStatus.IN_PROGRESS.value,
    )
    return data

# Input from Kafka topic
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, topics=[input_topic],
                                   add_config=producer_config))

messages = op.map(
    "update_status_in_progress",
    kafka_input,
    update_status_in_progress,
)

# Fetch and emit each commit individually
processed_commits = op.flat_map(
    "fetch_and_emit_commits",
    messages,
    fetch_and_emit_commits,
)

# Key the stream by 'job_id'
keyed_docs = op.key_on("key_by_job_id", processed_commits, extract_job_id)

# Collect batches of records keyed by the same job_id
batched_docs = op.collect("collect_docs", keyed_docs, timeout=timedelta(seconds=1), max_size=50)

# Remove the job_id key
keyless_docs = op.map("remove_key", batched_docs, lambda x: x[1])

# Create KafkaSinkMessages for each serialized commit data
kafka_messages = op.map("create_kafka_messages", keyless_docs, lambda x: KafkaSinkMessage(None, orjson.dumps(x)))

# Output serialized data to Kafka
op.output("kafka-vector-raw-add", kafka_messages,
          KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config, ))  # to vector db
op.output("kafka-output", kafka_messages,
          KafkaSink(brokers=brokers, topic=config.PROCESSED_TOPIC, add_config=producer_config, ))  # to local llm
