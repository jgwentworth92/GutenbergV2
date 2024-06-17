import orjson
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage


def github_message_handler(msg):
    resource_data = msg.get("resource_data")
    return KafkaSinkMessage(None, orjson.dumps(resource_data), topic="github_topic")


RESOURCE_HANDLER_MAPPING = {"github": github_message_handler}
