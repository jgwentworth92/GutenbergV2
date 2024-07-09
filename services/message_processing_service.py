from typing import Dict, Any, Generator, List
from logging_config import get_logger
from utils.langchain_callback_logger import MyCustomHandler
from utils.model_utils import setup_chat_model
from models.document import Document
import time


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


def process_messages(documents: List[Document]) -> Generator[List[Document], None, None]:
    """
    Processes a batch of documents, generating summaries for each and collecting the results.

    Args:
        documents (List[Document]): A list of Document objects to be processed.

    Yields:
        Generator[List[Document], None, None]: A generator yielding a list of Document objects, each containing either the raw or processed document.
    """
    start_time = time.time()

    try:
        handler = MyCustomHandler(logger)

        if not documents:
            logger.warning("No valid documents to process.")
            return

        logger.info(f"Processing {len(documents)} documents.")
        logger.info(f"First document metadata: {documents[0].metadata}")

        batch_inputs = prepare_batch_inputs(documents)
        chain = setup_chat_model()
        batch_results = chain.batch(batch_inputs, config={"max_concurrency": 5, "callbacks": [handler]})

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

        yield combined_results

    except ValueError as e:
        logger.error({"error": "Invalid document format", "details": str(e), "data":documents})
    except Exception as e:
        logger.error({"error": "Failed to process messages", "details": str(e), "data": documents})
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process {len(documents)} documents: {total_time:.2f} seconds")