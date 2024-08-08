from bytewax.dataflow import Dataflow
import bytewax.operators as op
import bytewax.operators as op
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from bytewax.dataflow import Dataflow
from confluent_kafka import OFFSET_STORED
from icecream import ic

from config.config_setting import config
from dataflows.github_commit_processing import serialize_standardized_message
from logging_config import setup_logging, get_logger
from models import constants
from services.message_processing_service import process_messages
from utils.status_update import StandardizedMessage, create_status_updater

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


def kafka_to_standardized(msg: KafkaSourceMessage) -> StandardizedMessage:
    data = orjson.loads(msg.value)
    return StandardizedMessage(
        job_id=data["job_id"],
        step_number=3,  # Assuming this is the second step in the overall process
        data=data,
        metadata={"original_topic": msg.topic}
    )


# Create KafkaSource for consuming messages from Kafka
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, topics=[input_topic], add_config=consumer_config))

standardized_messages = op.map(
    "kafka_to_standardized",
    kafka_input,
    kafka_to_standardized,
)
status_updater = create_status_updater(constants.Service.DATAFLOW_TYPE_processing_llm)

processed_messages = op.flat_map("process_message", standardized_messages,
                                 status_updater(process_messages))


def document_dump(processed_docs):
    return [doc.model_dump_json() for doc in processed_docs]  # Convert each Document to JSON string


serialized_docs = op.map("serialize_documents", processed_messages , serialize_standardized_message)

kafka_messages = op.map("create_kafka_messages", serialized_docs, lambda x: KafkaSinkMessage(None, x))

op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic))
