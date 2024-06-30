from datetime import timedelta
import bytewax.operators as op
import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from bytewax.dataflow import Dataflow
from config.config_setting import config
from logging_config import setup_logging
from services.pdf_processing_service import process_pdf

setup_logging()
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

# Process PDF and emit each document individually
processed_docs = op.flat_map("pdf processing", kafka_input,
                                lambda msg: process_pdf(orjson.loads(msg.value)))


keyed_docs = op.key_on("add_key", processed_docs, lambda doc: "pdf_key")
batched_docs = op.collect("collect_docs", keyed_docs, timeout=timedelta(seconds=1), max_size=50)

# Remove the key from the batched documents
keyless_docs = op.map("remove_key", batched_docs, lambda x: (None, x[1]))

# Create KafkaSinkMessages for each serialized document data
kafka_messages = op.map("create_kafka_messages", keyless_docs, lambda x: KafkaSinkMessage(None, orjson.dumps(x[1])))

# Output serialized data to Kafka
op.output("kafka-raw-pdf-add", kafka_messages, KafkaSink(brokers=brokers, topic=config.PROCESSED_TOPIC, add_config=producer_config))
op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=config.OUTPUT_TOPIC, add_config=producer_config)) # to local llm
