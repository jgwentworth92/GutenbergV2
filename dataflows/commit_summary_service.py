from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from confluent_kafka import OFFSET_END
from config.config_setting import config
from services.message_processing_service import process_message
from utils.kafka_utils import inspect_output_topic
import orjson
from confluent_kafka import OFFSET_STORED

# Application setup
brokers = [config.BROKERS]
input_topic = config.OUTPUT_TOPIC
output_topic = config.PROCESSED_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG

# Bytewax dataflow setup
flow = Dataflow("commit_summary_service")

# Create KafkaSource for consuming messages from Kafka
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, topics=[input_topic],
                                   add_config=consumer_config))

# Process each message
processed_messages = op.flat_map("process_message", kafka_input,
                                 lambda msg: process_message(orjson.loads(msg.value)))

# Serialize processed documents
serialized_messages = op.map("serialize_messages", processed_messages, orjson.dumps)

# Create KafkaSinkMessages for each serialized document
kafka_messages = op.map("create_kafka_messages", serialized_messages, lambda x: KafkaSinkMessage(None, x))

# Output serialized messages to Kafka
op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config))

# Input from Kafka to inspect output topic messages
kafka_output_input = op.input("kafka-output-input", flow,
                              KafkaSource(brokers=brokers, topics=[output_topic],
                                          add_config=consumer_config))

# Inspect the output topic messages
