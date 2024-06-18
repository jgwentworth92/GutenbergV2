import orjson

from config.config_setting import config

from icecream import ic

from bytewax import operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage, KafkaSourceMessage
from bytewax.dataflow import Dataflow


from confluent_kafka import OFFSET_STORED


# Bytewax dataflow setup
flow = Dataflow("Gateway Service")
ic(f"the stored offset is {OFFSET_STORED}")


RESOURCE_TOPIC_MAPPING = {"github": config.GITHUB_TOPIC, "pdf": config.PDF_INPUT}

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


def process_message(msg: KafkaSourceMessage):
    data = orjson.loads(msg.value)
    row = data["payload"]["after"]
    resource_type = row["resource_type"]
    return KafkaSinkMessage(
        None, orjson.dumps(row), topic=RESOURCE_TOPIC_MAPPING[resource_type]
    )


processed_messages = op.map(
    "process_message",
    kafka_input,
    process_message,
)

op.output(
    "kafka-output", processed_messages, KafkaSink(brokers=[config.BROKERS], topic=None)
)
