from typing import Dict, Any, Generator, List
from logging_config import get_logger
from models import constants
from utils.langchain_callback_logger import MyCustomHandler
from utils.model_utils import setup_chat_model
from models.document import Document
import time

from utils.status_update import StandardizedMessage, status_updater

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


@status_updater(constants.Service.DATAFLOW_TYPE_processing_llm)
def process_raw_data_with_llm_and_status(message: StandardizedMessage):
    return process_raw_data_with_llm(message)


def process_raw_data_with_llm(message: StandardizedMessage) -> Generator[List[Document], None, None]:
    start_time = time.time()
    job_id = message.job_id
    try:
        documents = [Document.model_validate_json(doc_json) for doc_json in message.data]
        handler = MyCustomHandler(logger)
        config = {"max_concurrency": 5, "callbacks": [handler]}
        if not documents:
            logger.warning("No valid documents to process.")
            return

        logger.info(f"Processing {len(documents)} documents.")
        logger.info(f"First document metadata: {documents[0].metadata}")

        batch_inputs = prepare_batch_inputs(documents)
        logger.info(f"the passed in model is {message.llm_model} with prompt{message.prompt}")
        # Use the prompt from the message if available, otherwise use None
        chain = setup_chat_model(custom_prompt=message.prompt,llm_model=message.llm_model)

        batch_results = chain.batch(batch_inputs, config=config)

        combined_results = []

        for i, summary in enumerate(batch_results):
            document = documents[i]
            combined_results.append(document)

            metadata = document.metadata.copy()
            metadata["vector_id"] = f"{metadata['vector_id']}_llm"
            metadata["doc_type"] = "SUMMARY"
            updated_doc = Document(
                page_content="Summary: " + summary,
                metadata=metadata
            )
            combined_results.append(updated_doc)

        yield StandardizedMessage(
            job_id=job_id,
            step_number=message.step_number,
            data=[doc.model_dump_json() for doc in combined_results],
            metadata={**message.metadata, "document_count": len(batch_results)}
            # Note: We don't include the prompt here as it's not needed in the output
        )
    except ValueError as e:
        logger.error({"error": "Invalid document format", "details": str(e), "data": message})
    except Exception as e:
        logger.error({"error": "Failed to process messages", "details": str(e), "data": message})
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process documents: {total_time:.2f} seconds")