from datetime import timedelta

import bytewax.operators as op
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSourceMessage
from bytewax.dataflow import Dataflow

from config.config_setting import config
from dataflow_connectors.HTTP_connector import HTTPSink
from logging_config import setup_logging, get_logger
from models import constants
from services.vectordb_service import insert_into_vectordb_with_status

from utils.dataflow_processing_utils import prepare_payload, kafka_to_standardized
from utils.status_update import StandardizedMessage, status_updater

setup_logging()
logger = get_logger(__name__)

# Application setup
brokers = config.BROKERS
llm_processed_topic = config.PROCESSED_TOPIC
consumer_config = config.CONSUMER_CONFIG
auth_header = {"Accept": "application/json", "Content-Type": "application/json"}

# Create Bytewax dataflow
flow = Dataflow("vector_db_insertion_service")

# Create KafkaSource for consuming messages from Kafka
vectordb_input = op.input("llm-processed-in", flow,
                          KafkaSource(brokers=[brokers], topics=[llm_processed_topic], add_config=consumer_config))





standardized_messages = op.map(
    "standardize_llm_processed",
    vectordb_input,
    kafka_to_standardized,
)

vectordb_inserted_messages = op.flat_map("insert_into_vectordb", standardized_messages,
                                         insert_into_vectordb_with_status)
valid_messages = op.filter("filter_valid_messages", vectordb_inserted_messages, lambda msg: msg is not None)
keyed_messages = op.map("key_by_job_id", valid_messages, lambda x: (x["job_id"], x))

# Collect batches of records keyed by the same job_id
batched_messages = op.collect(
    "batch_records_by_key",
    keyed_messages,
    timeout=timedelta(seconds=1),  # Collect into batches every 5 seconds
    max_size=100  # or when the batch size reaches 100
)

# Remove the key from the batched messages
keyless_docs = op.map("remove_key", batched_messages, lambda x: x[1])

# Output to the FastAPI using the HTTPSink
op.output("vectordb-batch-output", keyless_docs, HTTPSink(config.DOCUMENT_BATCH_ENDPOINT, auth_header, prepare_payload))
