import hashlib
import json
import uuid
from typing import Generator, Dict, Any, List

from config.config_setting import config
from logging_config import get_logger
from models import constants
from models.document import Document
from utils.get_qdrant import get_qdrant_vector_store
from utils.model_utils import setup_embedding_model
from utils.status_update import StandardizedMessage, status_updater

logging = get_logger(__name__)

def generate_uuid_from_string(val: str) -> uuid.UUID:
    """
    Generates a UUID based on a given string using MD5 hashing.

    Args:
        val (str): The string to generate the UUID from.

    Returns:
        uuid.UUID: The generated UUID.
    """
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    logging.info(f"id produced {hex_string}")
    return uuid.UUID(hex=hex_string)

@status_updater(constants.Service.DATAFLOW_TYPE_DATASINK)
def insert_into_vectordb_with_status(message: StandardizedMessage):
    return process_message_to_vectordb(message)
def process_message_to_vectordb(message:StandardizedMessage) -> Generator[Dict[str, Any], None, None]:
    """
    Processes a message containing documents and stores them in a vector database.

    Args:
        message (List[str]): The message containing a list of JSON strings of documents to be processed.

    Yields:
        Generator[Dict[str, Any], None, None]: A generator yielding the result of the operation, including any errors.
    """
    try:
        parsed_docs = [json.loads(doc) for doc in message.data['data']]

        # Then, validate each parsed JSON object as a Document
        documents = [Document.model_validate(doc) for doc in parsed_docs]
        logging.debug(f"Processing documents to VectorDB: {documents}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON in message: {e}")
        return
    except Exception as e:
        logging.error(f"Failed to validate documents: {e} with message {message}")
        return

    try:
        collection_name = documents[0].metadata['collection_name']
        job_id = documents[0].metadata['job_id']
        logging.info(f"Received request for {documents[0].metadata['collection_name']}")
        embed = setup_embedding_model()
        vectordb = get_qdrant_vector_store(host=config.VECTOR_DB_HOST, port=config.VECTOR_DB_PORT,
                                           embeddings=embed, collection_name=collection_name)

        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [str(generate_uuid_from_string(f"{doc.metadata.get('vector_id')}")) for doc in documents]

        added_ids = vectordb.add_texts(texts=texts, metadatas=metadatas, ids=ids)

        logging.info(f"Processed {len(added_ids)} documents into vectordb collection")
        for id, metadata in zip(ids, metadatas):
            result_message = {
                "collection_name": collection_name,
                "vector_db_id": id,
                "job_id": job_id,
                "document_type": metadata.get('doc_type', 'UNKNOWN')
            }
            yield result_message
    except Exception as e:
        logging.error(f"Failed to add documents to Qdrant: {e}")

