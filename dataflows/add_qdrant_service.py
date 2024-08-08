from datetime import timedelta

import bytewax.operators as op
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSourceMessage
from bytewax.dataflow import Dataflow

from config.config_setting import config
from dataflow_connectors.HTTP_connector import HTTPSink
from logging_config import setup_logging, get_logger
from models import constants
from services.vectordb_service import process_message_to_vectordb
from utils.dataflow_processing_utils import prepare_payload
from utils.status_update import StandardizedMessage, create_status_updater

setup_logging()
logger = get_logger(__name__)

# Application setup
brokers = config.BROKERS
input_topic = config.PROCESSED_TOPIC
consumer_config = config.CONSUMER_CONFIG
auth_header = {"Accept": "application/json", "Content-Type": "application/json"}

# Create Bytewax dataflow
flow = Dataflow("add_to_vector_db_service")

# Create KafkaSource for consuming messages from Kafka
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=[brokers], topics=[input_topic], add_config=consumer_config))
def kafka_to_standardized(msg: KafkaSourceMessage) -> StandardizedMessage:
    data = orjson.loads(msg.value)
    return StandardizedMessage(
        job_id=data["job_id"],
        step_number=4,  # Assuming this is the second step in the overall process
        data=data,
        metadata={"original_topic": msg.topic}
    )

messages = op.map(
    "update_status_in_progress",
    kafka_input,
    kafka_to_standardized,
)

status_updater = create_status_updater(constants.Service.DATAFLOW_TYPE_DATASINK)
# Process each message and update status
processed_messages = op.flat_map("process_and_update_status", messages,status_updater(process_message_to_vectordb))
keyed_messages = op.map("key_by_job_id", processed_messages, lambda x: (x["job_id"], x))

# Collect batches of records keyed by the same job_id
batched_messages = op.collect(
    "batch_records_by_key",
    keyed_messages,
    timeout=timedelta(seconds=5),  # Collect into batches every 10 seconds
    max_size=100  # or when the batch size reaches 10
)

# Define API settings for the custom sink
keyless_docs = op.map("remove_key", batched_messages, lambda x: (x[1]))

# Output to the FastAPI using the HTTPSink
op.output("api-output", keyless_docs, HTTPSink(config.DOCUMENT_BATCH_ENDPOINT, auth_header, prepare_payload))
# Define API settings for the custom sink
