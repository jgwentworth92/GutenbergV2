from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from confluent_kafka import OFFSET_END
from icecream import ic
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from config.config_setting import config
from services.message_processing_service import process_message
from services.vectordb_service import process_message_to_vectordb
from utils.get_qdrant import get_qdrant_vector_store
from utils.kafka_utils import inspect_output_topic
import orjson
from confluent_kafka import OFFSET_STORED
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from config.config_setting import config

from utils.kafka_utils import inspect_output_topic
import orjson
import logging
from pydantic import BaseModel
from typing import List, Dict, Any, Generator

# Application setup
brokers = [config.BROKERS]
input_topic = config.PROCESSED_TOPIC
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG


# Application setup

output_topic = config.VECTORDB_TOPIC_NAME


# Bytewax dataflow setup
flow = Dataflow("add_to_vector_db_service")





# Create KafkaSource for consuming messages from Kafka
ic(f"the stored offset is {OFFSET_STORED}")

# Create KafkaSource for consuming messages from Kafka
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, topics=[input_topic],
                                   add_config=consumer_config))

# Process each message and add to vector db
processed_messages = op.flat_map("process_message_to_vectordb", kafka_input,
                                 lambda msg: process_message_to_vectordb(orjson.loads(msg.value)))

# Serialize processed results
serialized_messages = op.map("serialize_messages", processed_messages, orjson.dumps)

# Create KafkaSinkMessages for each serialized result
kafka_messages = op.map("create_kafka_messages", serialized_messages, lambda x: KafkaSinkMessage(None, x))

# Output results to Kafka
op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config))

# Input from Kafka to inspect output topic messages
kafka_output_input = op.input("kafka-output-input", flow,
                              KafkaSource(brokers=brokers, topics=[output_topic],
                                          add_config=consumer_config))

# Inspect the output topic messages

