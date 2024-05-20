from kafka.errors import KafkaError
from icecream import ic
import orjson

def inspect_output_topic(index, message):
    if isinstance(message, KafkaError):
        ic(f"Error: {message}")
    else:
        ic(orjson.loads(message.value))
