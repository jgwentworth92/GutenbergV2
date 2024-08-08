import bytewax.operators as op
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from bytewax.dataflow import Dataflow
from confluent_kafka import OFFSET_STORED
from icecream import ic

from config.config_setting import config
from logging_config import setup_logging, get_logger
from models import constants
from services.github_service import fetch_and_emit_commits, fetch_and_emit_commits_with_status
from utils.status_update import status_updater, StandardizedMessage

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


def kafka_to_standardized(msg: KafkaSourceMessage) -> StandardizedMessage:
    data = orjson.loads(msg.value)
    return StandardizedMessage(
        job_id=data["job_id"],
        step_number=2,  # Assuming this is the second step in the overall process
        data=data,
        metadata={"original_topic": msg.topic}
    )


standardized_messages = op.map(
    "kafka_to_standardized",
    kafka_input,
    kafka_to_standardized,
)

# Apply the status updater decorator to fetch_and_emit_commits


# Use the decorated function in the dataflow
processed_commits = op.flat_map(
    "fetch_and_emit_commits_with_status",
    standardized_messages,
    fetch_and_emit_commits_with_status
)


def serialize_standardized_message(msg: StandardizedMessage):
    return msg.model_dump_json()


serialized_docs = op.map("serialize_documents", processed_commits, serialize_standardized_message)

kafka_messages = op.map("create_kafka_messages", serialized_docs, lambda x: KafkaSinkMessage(None, x))

# Output serialized data to Kafka
op.output("kafka-vector-raw-add", kafka_messages,
          KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config))
