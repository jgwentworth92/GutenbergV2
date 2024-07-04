import orjson
from typing import Dict, Any, Generator, List
from logging_config import get_logger
from utils.langchain_callback_logger import MyCustomHandler
from utils.model_utils import setup_chat_model
from models.document import Document
import time

from models import constants
from utils.dataflow_processing_utils import  extract_job_id
from services.user_management_service import user_management_service


logger = get_logger(__name__)


def prepare_batch_inputs(documents: List[Document]) -> List[Dict[str, str]]:
    """
    Prepares batch inputs for processing.

    Args:
        documents (List[Document]): A list of Document objects.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the document content.
    """

    return [{"text": doc.page_content} for doc in documents]


def process_messages(messages: List[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Processes a batch of documents, generating summaries for each and collecting the results.

    Args:
        messages (List[str]): A list of JSON strings representing the documents to be processed.

    Yields:
        Generator[Dict[str, Any], None, None]: A generator yielding a dictionary containing the processed documents.
    """
    start_time = time.time()

    try:
        handler = MyCustomHandler(logger)
        documents = [Document.model_validate_json(doc_json) for doc_json in messages]
        job_ids = set(extract_job_id(doc) for doc in messages)
        for job_id in job_ids:
            user_management_service.update_status(
                constants.Service.COMMIT_SUMMARY,
                job_id,
                constants.StepStatus.IN_PROGRESS.value,
            )

        if not documents:
            logger.warning("No valid documents to process.")
            return

        logger.info(f"Processing {len(documents)} documents.")
        logger.info(f"First document metadata: {documents[0].metadata}")

        batch_inputs = prepare_batch_inputs(documents)
        chain = setup_chat_model()
        batch_results = chain.batch(batch_inputs, config={"max_concurrency": 5, "callbacks": [handler]})

        for i, summary in enumerate(batch_results):
            document = documents[i]
            metadata = document.metadata
            metadata["vector_id"] = f"{metadata['vector_id']}_llm"
            metadata["doc_type"] = "SUMMARY"
            updated_doc = Document(
                page_content="Summary: " + summary,
                metadata=metadata
            )
            yield updated_doc.model_dump_json()

    except (ValueError, orjson.JSONDecodeError) as e:
        logger.error({"error": "Invalid document format", "details": str(e), "data": messages})
    except Exception as e:
        for job_id in job_ids:
            user_management_service.update_status(
                constants.Service.COMMIT_SUMMARY,
                job_id,
                constants.StepStatus.FAILED.value,
            )
        logger.error({"error": "Failed to process messages", "details": str(e), "data": messages})
    else:
        for job_id in job_ids:
            user_management_service.update_status(
                constants.Service.COMMIT_SUMMARY,
                job_id,
                constants.StepStatus.COMPLETE.value,
            )
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process {len(messages)} documents: {total_time:.2f} seconds")
