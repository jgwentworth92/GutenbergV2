from typing import Generator, Dict, Any, List
from icecream import ic
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import FakeEmbeddings
from config.config_setting import config
from models.document import Document
from utils.get_qdrant import get_qdrant_vector_store
from utils.model_utils import setup_embedding_model
from utils.setup_logging import get_logger, setup_logging
import uuid
import hashlib

setup_logging()
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

def process_message_to_vectordb(message: List[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Processes a message containing documents and stores them in a vector database.

    Args:
        message (List[str]): The message containing a list of JSON strings of documents to be processed.

    Yields:
        Generator[Dict[str, Any], None, None]: A generator yielding the result of the operation, including any errors.
    """
    try:
        documents = [Document.parse_raw(doc) for doc in message]
        logging.debug(f"Processing documents to VectorDB: {documents}")
    except Exception as e:
        logging.error(f"Failed to parse documents: {e} with message {message}")
        return

    if not documents:
        logging.error("No valid documents found in the message")
        return


    try:
        collection_name = documents[0].metadata['collection_name']
        logging.info(f"Received request for {documents[0].metadata['id']}")
        embed = setup_embedding_model()
        vectordb = get_qdrant_vector_store(host=config.VECTOR_DB_HOST, port=config.VECTOR_DB_PORT,
                                           embeddings=embed, collection_name=collection_name)

        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [str(generate_uuid_from_string(f"{doc.metadata.get('vector_id')}")) for doc in documents]

        added_ids = vectordb.add_texts(texts=texts, metadatas=metadatas, ids=ids)

        result_message = {"collection_name": collection_name, "id": added_ids}
        logging.info(f"Processed {len(added_ids)} documents into vectordb collection")
        yield result_message
    except Exception as e:
        logging.error(f"Failed to add documents to Qdrant: {e}")

