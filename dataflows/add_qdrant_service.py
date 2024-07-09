import datetime
from datetime import timedelta
import orjson
from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource, KafkaSourceMessage
import bytewax.operators as op
from config.config_setting import config
from dataflow_connectors.HTTP_connector import HTTPSink
from logging_config import setup_logging, get_logger
from models import constants
from models.document import Document
from services.user_management_service import user_management_service
from services.vectordb_service import process_message_to_vectordb
from utils.dataflow_processing_utils import prepare_payload

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
def update_status_in_progress(msg: KafkaSourceMessage):
    messages = orjson.loads(msg.value)
    data = [Document.model_validate_json(doc_json) for doc_json in messages]

    row = data[0].metadata

    job_id = row["job_id"]
    logger.info(f"Updating status for job id {job_id}")
    user_management_service.update_status(
        job_id,
        constants.Service.DATAFLOW_TYPE_DATASINK.value,
        constants.StepStatus.IN_PROGRESS.value,
    )
    return data
# Process each message to extract vector DB information
processed_messages = op.flat_map("process_message_to_vectordb", kafka_input,
                                 lambda msg: process_message_to_vectordb(orjson.loads(msg.value)))

# Key the stream by 'job_id' for consistent batching
keyed_messages = op.map("key_by_job_id", processed_messages, lambda x: (x["job_id"], x))

# Collect batches of records keyed by the same job_id
batched_messages = op.collect(
    "batch_records_by_key",
    keyed_messages,
    timeout=timedelta(seconds=10),  # Collect into batches every 10 seconds
    max_size=100  # or when the batch size reaches 10
)

# Define API settings for the custom sink
keyless_docs = op.map("remove_key", batched_messages, lambda x: (x[1]))

# Output to the FastAPI using the HTTPSink
op.output("api-output", keyless_docs, HTTPSink(config.DOCUMENT_BATCH_ENDPOINT, auth_header, prepare_payload))
