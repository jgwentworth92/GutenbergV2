from typing import Generator
from langchain_community.document_loaders.pdf import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from orjson import orjson
from logging_config import get_logger
from models.document import Document
from utils.status_update import StandardizedMessage, status_updater
from models import constants

logger = get_logger(__name__)


@status_updater(constants.Service.DATAFLOW_TYPE_processing_raw)
def process_pdf(message: StandardizedMessage) -> Generator[StandardizedMessage, None, None]:
    """
    Processes a PDF document, generating chunks for each page.

    Args:
        message (StandardizedMessage): A standardized message containing the PDF processing information.

    Yields:
        Generator[StandardizedMessage, None, None]: A generator yielding StandardizedMessage objects containing the processed documents.
    """
    try:
        resource_data = orjson.loads(message.data["resource_data"])
        job_id = message.job_id
        pdf_url = resource_data["pdf_url"]
        collection = resource_data["collection_name"]
        prompt = resource_data.get("prompt")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        loader = PyMuPDFLoader(pdf_url)
        docs = loader.load()

        texts = text_splitter.split_documents(docs)
        processed_docs = []

        for i, doc in enumerate(texts):
            extra_metadata = {
                "collection_name": collection,
                "job_id": job_id,
                "doc_type": "raw",
                "vector_id": f"{pdf_url} page {str(doc.metadata['page'])} for chunk {str(i + 1)}"
            }
            combined_metadata = {**doc.metadata, **extra_metadata}
            processed_doc = Document(page_content=doc.page_content, metadata=combined_metadata)
            processed_docs.append(processed_doc.model_dump_json())

        if processed_docs:
            yield StandardizedMessage(
                job_id=job_id,
                step_number=message.step_number,
                data=processed_docs,
                metadata={**message.metadata, "pdf_url": pdf_url, "document_count": len(processed_docs)},
                prompt=prompt
            )
            logger.info(f"Processed PDF into {len(processed_docs)} documents for job {job_id}")
        else:
            logger.warning(f"No documents created for job {job_id}")

    except Exception as e:
        logger.error({
            "error": "Failed to process PDF",
            "details": str(e),
        })
