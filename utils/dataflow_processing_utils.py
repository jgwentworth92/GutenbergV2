import datetime
from typing import Any, Callable, Iterable, Optional

from bytewax.connectors.kafka import KafkaSourceMessage
from orjson import orjson

from logging_config import get_logger
from models import constants
from models.document import Document
from services.user_management_service import user_management_service

logger = get_logger(__name__)


def extract_job_id(document):
    doc = orjson.loads(document)
    return document.get('metadata', {}).get('job_id', 'default_job_id')


def extract_job_id_documents(message):
    try:
        if isinstance(message, list) and message and isinstance(message[0], Document):
            # Input is already a list of Document objects
            data = message
        else:
            # Input is JSON, parse it into Document objects
            data = [Document.model_validate_json(doc_json) for doc_json in message]

        if not data:
            raise ValueError("Empty data list")

        row = data[0].metadata
        job_id = row.get("job_id")

        if not job_id:
            raise ValueError("job_id not found in document metadata")

        return job_id
    except Exception as e:
        logger.error(f"Error getting job id: {e}")
        return None

def update_status_in_progress_documents(msg: KafkaSourceMessage):
    messages = orjson.loads(msg.value)
    data = [Document.model_validate_json(doc_json) for doc_json in messages]

    row = data[0].metadata

    job_id = row["job_id"]
    logger.info(f"Updating status for job id {job_id}")
    user_management_service.update_status(
        job_id,
        constants.Service.DATAFLOW_TYPE_processing_llm.value,
        constants.StepStatus.IN_PROGRESS.value,
    )
    return data


def create_process_and_update_status(
        service: constants.Service,
        processing_func: Callable[[Any], Iterable[Any]],
        job_id_func: Callable[[Any], Optional[str]]
) -> Callable[[Any], Iterable[Any]]:
    """
    Creates a function that processes data, updates status, and handles errors.
    This function is compatible with Bytewax operators and allows for custom job ID extraction.

    :param service: The service type (e.g., DATAFLOW_TYPE_DATASINK)
    :param processing_func: The function to process the data
    :param job_id_func: Function to extract job ID from the input data
    :return: A function that can be used with Bytewax operators
    """

    def process_and_update_wrapper(data: Any) -> Iterable[Any]:
        job_id = job_id_func(data)
        if job_id is None:
            logger.error("Unable to extract job_id from data")
            return []
        try:
            processed_data = list(processing_func(data))

            if not processed_data:
                raise Exception("No data processed")

            logger.info(f"Updating status to COMPLETE for job id {job_id}")
            user_management_service.update_status(
                job_id,
                service.value,
                constants.StepStatus.COMPLETE.value,
            )

            return processed_data
        except Exception as e:
            logger.error(f"Error processing data for job id {job_id}: {e}")
            user_management_service.update_status(
                job_id,
                service.value,
                constants.StepStatus.FAILED.value,
            )
            return []

    return process_and_update_wrapper


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
