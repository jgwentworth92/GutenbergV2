from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import operators as kop ,KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from icecream import ic
from config.config_setting import config
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from confluent_kafka import OFFSET_STORED
from icecream import ic
from config.config_setting import config
from dataflows.github_commit_processing import serialize_standardized_message
from logging_config import setup_logging, get_logger
from services.message_processing_service import process_raw_data_with_llm_and_status
from utils.dataflow_processing_utils import kafka_to_standardized
from utils.status_update import StandardizedMessage


setup_logging()
logger = get_logger(__name__)
# Application setup
logger = get_logger(__name__)
brokers = [config.BROKERS]
raw_data_topic = config.OUTPUT_TOPIC
llm_processed_topic = config.PROCESSED_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG

# Bytewax dataflow setup
flow = Dataflow("llm_raw_data_processing_service")
ic(f"the stored offset is {OFFSET_STORED}")





# Create KafkaSource for consuming messages from Kafka
raw_data_input = op.input("raw-data-in", flow,
                          KafkaSource(brokers=brokers, topics=[raw_data_topic], add_config=consumer_config))

standardized_messages = op.map(
    "standardize_raw_data",
    raw_data_input,
    kafka_to_standardized,
)

llm_processed_messages = op.flat_map("process_with_llm", standardized_messages, process_raw_data_with_llm_and_status)
filtered_commits = op.filter(
    "filter_empty_messages",
    llm_processed_messages,
    lambda msg: msg is not None and bool(msg)
)

serialized_llm_docs = op.map("serialize_llm_documents", filtered_commits , serialize_standardized_message)

kafka_messages = op.map("create_kafka_messages", serialized_llm_docs, lambda x: KafkaSinkMessage(None, x))

op.output("llm-processed-output", kafka_messages, KafkaSink(brokers=brokers, topic=llm_processed_topic))
