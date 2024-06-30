import json
from datetime import timedelta
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import operators as kop, KafkaSource, KafkaSink, KafkaSinkMessage
from icecream import ic
from config.config_setting import config
import orjson
from confluent_kafka import OFFSET_STORED
from logging_config import setup_logging
from services.message_processing_service import process_messages
from utils.dataflow_processing_utils import parse_and_extract_job_id, extract_job_id

setup_logging()
# Application setup
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

# Process each message
processed_messages = op.flat_map("process_message", kafka_input.oks,
                                 lambda msg: process_messages(orjson.loads(msg.value)))


keyed_docs = op.key_on("key_by_job_id", processed_messages, extract_job_id)


# Collect batches of records keyed by the same job_id
batched_docs = op.collect(
    "batch_records_by_key",
    keyed_docs ,
    timeout=timedelta(seconds=1),
    max_size=50
)


# Create a single KafkaSinkMessage for each batch
keyless_docs = op.map("remove_key", batched_docs, lambda x: x[1])

# Create KafkaSinkMessages for each serialized commit data
kafka_messages = op.map("create_kafka_messages", keyless_docs, lambda x: KafkaSinkMessage(None, orjson.dumps(x)))

op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic))
