from typing import Dict, Any, Generator, List
from utils.model_utils import setup_chat_model
from utils.setup_logging import get_logger, setup_logging
from multiprocessing import Pool
import time

setup_logging()
logger = get_logger(__name__)

def process_document(document: Dict[str, Any]) -> Dict[str, Any]:
    try:
        chain = setup_chat_model()
        summary = chain.invoke({"text": document["page_content"]})
        metadata = document["metadata"]
        metadata["vector_id"] = f"{metadata['vector_id']}_llm"
        updated_doc = {
            "page_content": "Summary: " + summary,
            "metadata": metadata
        }
        logger.info(f"Processed metadata of document with vector_id {metadata['vector_id']}")
        return updated_doc
    except Exception as e:
        error_message = {
            "error": "Failed to process document",
            "details": str(e),
            "document_metadata": document["metadata"]
        }
        logger.error(error_message)

def process_messages(messages: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    start_time = time.time()
    processed_results = []

    try:
        with Pool() as pool:
            documents = messages["documents"]
            for result in pool.imap_unordered(process_document, documents):
                if result:
                    logger.info(f"processed docuement with metadata {result['metadata']}")
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
            yield {"documents": processed_results}

# Example usage:
# messages = {"documents": [list of documents]}
# for result in process_messages(messages):
#     # handle the processed documents
