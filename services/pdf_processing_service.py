import time
from typing import Dict, Any, Generator, List
from langchain_community.document_loaders.pdf import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from orjson import orjson
from logging_config import get_logger
from models.document import Document

logger = get_logger(__name__)

def process_pdf(messages: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """
    Processes a batch of documents, generating summaries for each and collecting the results.

    Args:
        messages (List[str]): A list of JSON strings representing the documents to be processed.

    Yields:
        Generator[Dict[str, Any], None, None]: A generator yielding a dictionary containing the processed documents.
    """
    start_time = time.time()

    try:
        data=orjson.loads(messages["resource_data"])
        job_id=messages["job_id"]
        pdf_url = data["pdf_url"]
        collection = data["collection_name"]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        loader = PyMuPDFLoader(pdf_url)
        docs = loader.load()

        final_output = []
        page_number = 1
        texts = text_splitter.split_documents(docs)
        for doc in texts:
            page_number += 1

            extra_metadata = {
                "collection_name": collection,
                "job_id": job_id,
                "doc_type":"raw",
                "vector_id": f"{pdf_url} page {str(doc.metadata['page'])} for chunk {str(page_number)}"
            }
            combined_metadata = {**doc.metadata, **extra_metadata}
            doc_document = Document(page_content=doc.page_content, metadata=combined_metadata)
            yield doc_document.model_dump_json()


    except Exception as e:
        error_message = {
            "error": "Failed to process messages",
            "details": str(e),
            "data": messages
        }
        logger.error(error_message)
        return
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process documents: {total_time:.2f} seconds")
