from bytewax import operators as op
from bytewax.connectors.kafka import (
    KafkaSource,
    KafkaSink,
)
from bytewax.dataflow import Dataflow
from config.config_setting import config
from logging_config import get_logger, setup_logging
from services.gateway_routing import  process_and_route_message, kafka_to_standardized

setup_logging()
logger = get_logger(__name__)

flow = Dataflow("Gateway Service")


# Define the dataflow
kafka_input = op.input(
    "read-kafka-message",
    flow,
    KafkaSource(
        brokers=[config.BROKERS],
        topics=[config.RESOURCE_TOPIC],
        add_config=config.CONSUMER_CONFIG,
    ),
)

standardized_messages = op.map("kafka_to_standardized", kafka_input, kafka_to_standardized)
processed_messages = op.map("process_and_route_messages", standardized_messages, process_and_route_message)

# Filter out None values
valid_messages = op.filter(
    "unwrap_and_filter_valid_messages",
    processed_messages,
    lambda result: result and isinstance(result, list) and len(result) > 0 and result[0] is not None
)
unwrapped_messages = op.map(
    "extract_kafka_sink_message",
    valid_messages,
    lambda result: result[0]
)

op.output("kafka-output", unwrapped_messages, KafkaSink(brokers=[config.BROKERS], topic=None))


