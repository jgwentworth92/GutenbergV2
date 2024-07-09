import json
from datetime import timedelta
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import operators as kop, KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from icecream import ic
from config.config_setting import config
import orjson
from confluent_kafka import OFFSET_STORED
from logging_config import setup_logging, get_logger
from models import constants
from models.document import Document
from services.user_management_service import user_management_service
from services.message_processing_service import process_messages
from utils.dataflow_processing_utils import extract_job_id

setup_logging()
# Application setup
logger = get_logger(__name__)
brokers = [config.BROKERS]
input_topic = config.OUTPUT_TOPIC
output_topic = config.PROCESSED_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG

# Bytewax dataflow setup
flow = Dataflow("commit_summary_service")
ic(f"the stored offset is {OFFSET_STORED}")

# Create KafkaSource for consuming messages from Kafka
kafka_input = kop.input("kafka-in-2", flow, brokers=brokers, topics=[input_topic])
op.inspect("inspect_err", kafka_input.errs).then(op.raises, "raise_errors")


# Collect batches of records keyed by the same job_id
def update_status_in_progress(msg: KafkaSourceMessage):
    messages = orjson.loads(msg.value)
    data = [Document.model_validate_json(doc_json) for doc_json in messages]

    row = data[0].metadata

    job_id = row["job_id"]
    logger.info(f"Updating status for job id {job_id}")
    user_management_service.update_status(
        job_id,
        constants.Service.DATAFLOW_TYPE_processing_llm.value,
        constants.StepStatus.IN_PROGRESS.value,
    )
    return data  # Return the validated documents instead of the original message


# Process each message
messages = op.map(
    "update_status_in_progress",
    kafka_input.oks,
    update_status_in_progress,
)
processed_messages = op.flat_map("process_message", messages,
                                 lambda docs: process_messages(docs))


def update_status_complete(processed_docs):
    if processed_docs:
        job_id = processed_docs[0].metadata["job_id"]
        logger.info(f"Updating status to complete for job id {job_id}")
        user_management_service.update_status(
            job_id,
            constants.Service.DATAFLOW_TYPE_processing_llm.value,
            constants.StepStatus.COMPLETE.value,
        )
    return [doc.model_dump_json() for doc in processed_docs]  # Convert each Document to JSON string


completed_messages = op.map("update_status_complete", processed_messages, update_status_complete)
kafka_messages = op.map("create_kafka_messages", completed_messages, lambda x: KafkaSinkMessage(None, orjson.dumps(x)))

op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic))
