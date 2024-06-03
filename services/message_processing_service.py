from typing import Dict, Any, Generator, List
from utils.model_utils import setup_chat_model
from utils.setup_logging import get_logger, setup_logging
from multiprocessing import Pool
from models.document import Document
import time

setup_logging()
logger = get_logger(__name__)

def process_document(document: Document) -> Document:
    """
    Processes a single document by generating a summary and updating metadata.

    Args:
        document (Document): The document to process.

    Returns:
        Document: The updated Document object with a summary and updated metadata.
    """
    try:
        chain = setup_chat_model()
        summary = chain.invoke({"text": document.page_content})
        metadata = document.metadata
        metadata["vector_id"] = f"{metadata['vector_id']}_llm"
        updated_doc = Document(
            page_content="Summary: " + summary,
            metadata=metadata
        )
        logger.info(f"Processed metadata of document with vector_id {metadata['vector_id']}")
        return updated_doc
    except Exception as e:
        error_message = {
            "error": "Failed to process document",
            "details": str(e),
            "document_metadata": document.metadata
        }
        logger.error(error_message)


def process_messages(messages: List[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Processes a batch of documents, generating summaries for each and collecting the results.

    Args:
        messages (List[str]): A list of JSON strings representing the documents to be processed.

    Yields:
        Generator[Dict[str, Any], None, None]: A generator yielding a dictionary containing the processed documents.
    """
    start_time = time.time()
    processed_results = []

    try:
        documents = [Document.parse_raw(doc_json) for doc_json in messages]
        with Pool() as pool:
            for result in pool.imap_unordered(process_document, documents):
                if result:
                    logger.info(f"Processed document with metadata {result.metadata}")
                    processed_results.append(result)
    except Exception as e:
        error_message = {
            "error": "Failed to process messages",
            "details": str(e),
            "data": messages
        }
        logger.error(error_message)
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process documents: {total_time:.2f} seconds")

        if processed_results:
            yield [result.model_dump_json() for result in processed_results]


