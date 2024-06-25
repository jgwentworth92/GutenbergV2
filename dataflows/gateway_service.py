import orjson

from config.config_setting import config

from icecream import ic

from bytewax import operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from bytewax.dataflow import Dataflow


from confluent_kafka import OFFSET_STORED

from logging_config import setup_logging, get_logger

setup_logging()

logger = get_logger(__name__)

flow = Dataflow("Gateway Service")

RESOURCE_TOPIC_MAPPING = {"github": config.GITHUB_TOPIC, "pdf": config.PDF_INPUT}

kafka_input = op.input(
    "read-kafka-message",
    flow,
    KafkaSource(
        brokers=[config.BROKERS],
        topics=[config.RESOURCE_TOPIC],
        add_config=config.CONSUMER_CONFIG,
    ),
)


def process_message(msg: KafkaSourceMessage):
    data = orjson.loads(msg.value)
    row = data["payload"]["after"]
    resource_type = row["resource_type"]
    logger.info(f"data type submitted to gateway dataflow {resource_type} with payload: {row}")

    if resource_type in RESOURCE_TOPIC_MAPPING:
        return KafkaSinkMessage(
            None, orjson.dumps(row), topic=RESOURCE_TOPIC_MAPPING[resource_type]
        )
    return None


processed_messages = op.map(
    "process_message",
    kafka_input,
    process_message,
)

# Filter out None values
valid_messages = op.filter(
    "filter_valid_messages",
    processed_messages,
    lambda msg: msg is not None,
)

op.output(
    "kafka-output", valid_messages, KafkaSink(brokers=[config.BROKERS], topic=None)
)
