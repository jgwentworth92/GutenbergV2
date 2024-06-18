import orjson

from config.config_setting import config
from dataflows.gateway_service.resource_handler_mapping import RESOURCE_HANDLER_MAPPING

from icecream import ic

from bytewax import operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
from bytewax.dataflow import Dataflow


from confluent_kafka import OFFSET_STORED


# Bytewax dataflow setup
flow = Dataflow("Gateway Service")
ic(f"the stored offset is {OFFSET_STORED}")

def github_message_handler(msg):
    resource_data = msg.get("resource_data")
    return KafkaSinkMessage(None, orjson.dumps(resource_data), topic="github_topic")


RESOURCE_HANDLER_MAPPING = {"github": github_message_handler}

# Create KafkaSource for consuming messages from Kafka
kafka_input = op.input(
    "read-kafka-message",
    flow,
    KafkaSource(
        brokers=[config.BROKERS],
        topics=[config.RESOURCE_TOPIC],
        add_config=config.CONSUMER_CONFIG,
    ),
)


def process_message(msg):
    data = orjson.loads(msg.value)
    row = data["payload"]["after"]
    resource_type = row["resource_type"]
    return RESOURCE_HANDLER_MAPPING[resource_type](row)


processed_messages = op.map(
    "process_message",
    kafka_input,
    process_message,
)

op.output(
    "kafka-output", processed_messages, KafkaSink(brokers=[config.BROKERS], topic=None)
)
