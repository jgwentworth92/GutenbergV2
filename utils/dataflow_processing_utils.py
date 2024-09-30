import datetime

from bytewax.connectors.kafka import KafkaSourceMessage
from orjson import orjson
from logging_config import get_logger
from utils.status_update import StandardizedMessage

logger = get_logger(__name__)

def kafka_to_standardized(msg: KafkaSourceMessage) -> StandardizedMessage:
    data = orjson.loads(msg.value)
    payload = data["data"]

    # Create the base parameters for the StandardizedMessage object
    kwargs = {
        "job_id": data["job_id"],
        "step_number": data["step_number"] + 1,
        "data": payload,
        "metadata": {"original_topic": msg.topic}
    }

    # Add 'prompt' and 'llm_model' to kwargs if they are present in data
    if "prompt" in data:
        kwargs["prompt"] = data["prompt"]
    if "llm_model" in data:
        kwargs["llm_model"] = data["llm_model"]

    # Return the StandardizedMessage object with the dynamically updated fields
    return StandardizedMessage(**kwargs)


def prepare_payload(items) -> list:
    """
    Transform the data items into the required JSON structure for the FastAPI endpoint.

    :param items: List of dictionaries or a single dictionary containing the data.
    :return: List of dictionaries formatted for the FastAPI endpoint.
    """
    if not isinstance(items, list):
        items = [items]

    rtn = []
    for item in items:
        if isinstance(item, dict):
            item_copy = item.copy()
            item_copy["created_at"] = datetime.datetime.now().isoformat()
            item_copy["updated_at"] = datetime.datetime.now().isoformat()
            rtn.append(item_copy)
        else:
            # If the item is not a dictionary, we'll add it as is
            rtn.append(item)

    return rtn
