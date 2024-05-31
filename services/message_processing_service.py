from typing import Dict, Any, Generator, List
from utils.model_utils import setup_chat_model
from utils.setup_logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)



def process_message(message: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    if "error" in message:
        logger.error(f"Error in message: {message}")
        return
    event_data = message
    yield event_data
    try:

        try:
            chain = setup_chat_model()
            summary = chain.invoke({"text":event_data["page_content"]})
            updated_doc = {
                "page_content": "Summary: " + summary,
                "metadata": event_data["metadata"]
            }

            yield updated_doc
            logger.info(f"Metadata of commit {event_data['metadata']}")
        except Exception as e:
            error_message = {
                "error": "Failed to process document",
                "details": str(e),
                "document_metadata":event_data['metadata']
            }
            logger.error(error_message)
            yield error_message
    except Exception as e:
        error_message = {
            "error": "Failed to create documents",
            "details": str(e),
            "event_data": event_data
        }
        logger.error(error_message)
        yield error_message