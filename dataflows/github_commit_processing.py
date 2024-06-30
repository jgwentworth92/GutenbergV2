from datetime import timedelta
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from icecream import ic
from confluent_kafka import OFFSET_STORED
from config.config_setting import config
from logging_config import setup_logging
from services.github_service import fetch_and_emit_commits
import orjson
setup_logging()
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
                       KafkaSource(brokers=brokers,  topics=[input_topic],
                                   add_config=producer_config))

# Fetch and emit each commit individually
processed_commits = op.flat_map("fetch_and_emit_commits", kafka_input,
                                lambda msg: fetch_and_emit_commits(orjson.loads(msg.value)))



# Create KafkaSinkMessages for each serialized commit data
keyed_docs = op.key_on("add_key",processed_commits, lambda doc: "temp_key")
batched_docs = op.collect("collect_docs", keyed_docs, timeout=timedelta(seconds=1), max_size=50)
keyless_docs = op.map("remove_key", batched_docs, lambda x: (None, x[1]))
kafka_messages = op.map("create_kafka_messages", keyless_docs, lambda x: KafkaSinkMessage(None, orjson.dumps(x[1])))

# Output serialized data to Kafka
op.output("kafka-vector-raw-add", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config,)) # to vctor db
op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=config.PROCESSED_TOPIC, add_config=producer_config,)) # to local llm




