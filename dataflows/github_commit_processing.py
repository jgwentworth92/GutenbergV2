from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from confluent_kafka import OFFSET_END
from config.config_setting import config
from services.github_service import fetch_and_emit_commits
from utils.kafka_utils import inspect_output_topic
import orjson

# Application setup
brokers = [config.BROKERS]
input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG
from confluent_kafka import OFFSET_STORED

# Bytewax dataflow setup
flow = Dataflow("github_commit_processing")

# Input from Kafka topic
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers,  topics=[input_topic],
                                   add_config=consumer_config))

# Fetch and emit each commit individually
processed_commits = op.flat_map("fetch_and_emit_commits", kafka_input,
                                lambda msg: fetch_and_emit_commits(orjson.loads(msg.value)))

# Serialize each commit data
serialized_commits = op.map("serialize_commits", processed_commits, orjson.dumps)

# Create KafkaSinkMessages for each serialized commit data
kafka_messages = op.map("create_kafka_messages", serialized_commits, lambda x: KafkaSinkMessage(None, x))

# Output serialized data to Kafka
op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config))

# Input from Kafka, deserialize each message
kafka_output_input = op.input("kafka-output-input", flow,
                              KafkaSource(brokers=brokers,  topics=[output_topic],
                                          add_config=consumer_config))

# Inspect the output topic messages
op.inspect("inspect_output_topic", kafka_output_input, inspect_output_topic)
