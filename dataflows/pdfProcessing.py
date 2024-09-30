from datetime import timedelta
import bytewax.operators as op
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from bytewax.dataflow import Dataflow
from config.config_setting import config
from logging_config import setup_logging, get_logger
from services.pdf_processing_service import process_pdf, process_pdf_with_status
from utils.dataflow_processing_utils import kafka_to_standardized
from utils.status_update import StandardizedMessage

setup_logging()
logger = get_logger(__name__)

# Application setup
brokers = [config.BROKERS]
input_topic = config.PDF_INPUT
output_topic = config.OUTPUT_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG

# Bytewax dataflow setup
flow = Dataflow("pdf_processing")

# Input from Kafka topic
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, topics=[input_topic],
                                   add_config=producer_config))

# Convert Kafka messages to StandardizedMessage
standardized_messages = op.map(
    "kafka_to_standardized",
    kafka_input,
    kafka_to_standardized,
)

# Process PDF and emit each document individually
processed_docs = op.flat_map("pdf processing", standardized_messages, process_pdf_with_status)

# Filter out any None or empty messages
filtered_docs = op.filter(
    "filter_empty_messages",
    processed_docs,
    lambda msg: msg is not None and bool(msg.data)
)

# Serialize StandardizedMessages
serialized_docs = op.map("serialize_documents", filtered_docs, lambda x: x.model_dump_json())

# Create KafkaSinkMessages for each serialized document data
kafka_messages = op.map("create_kafka_messages", serialized_docs, lambda x: KafkaSinkMessage(None, x))

# Output serialized data to Kafka
op.output("kafka-raw-pdf-add", kafka_messages,
          KafkaSink(brokers=brokers, topic=config.PROCESSED_TOPIC, add_config=producer_config))
op.output("kafka-output", kafka_messages,
          KafkaSink(brokers=brokers, topic=config.OUTPUT_TOPIC, add_config=producer_config))