
from typing import Generator, Dict, Any

from icecream import ic
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import FakeEmbeddings


from config.config_setting import config
from utils.get_qdrant import get_qdrant_vector_store
from utils.model_utils import setup_embedding_model
from utils.setup_logging import get_logger, setup_logging

setup_logging()
logging = get_logger(__name__)
import uuid
import hashlib
def generate_uuid_from_string(val: str):
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    logging.info(f"id produced {hex_string}")

    return uuid.UUID(hex=hex_string)

def process_message_to_vectordb(message: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    try:
        documents = [Document(page_content=doc['page_content'], metadata=doc['metadata']) for doc in message["documents"]]
        logging.debug(f"Processing documents to VectorDB: {documents}")
    except Exception as e:
        logging.error(f"Failed to parse documents: {e}")
        yield {"error": "Failed to parse documents", "details": str(e)}
        return

    if not documents:
        logging.error("No valid documents found in the message")
        yield {"error": "No valid documents found", "details": message}
        return

    collection_name = documents[0].metadata.get('collection_name')
    logging.info(f"Received request for {documents[0].metadata.get('id')}")
    try:
        embed = setup_embedding_model()
        vectordb = get_qdrant_vector_store(host=config.VECTOR_DB_HOST, port=config.VECTOR_DB_PORT,
                                           embeddings=embed, collection_name=collection_name)

        # Extract text, metadata, and ids from documents
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Generate UUIDs from file name and commit ID
        ids = [str(generate_uuid_from_string(f"{doc.metadata.get('vector_id')}")) for doc in documents]

        # Use add_texts method to add documents with specific IDs
        added_ids = vectordb.add_texts(texts=texts, metadatas=metadatas, ids=ids)

        result_message = {"collection_name": collection_name, "id": added_ids}
        logging.info(f"Processed {len(added_ids)} documents into vectordb collection")
        yield result_message
    except Exception as e:
        logging.error(f"Failed to add documents to Qdrant: {e}")
        yield {"error": "Failed to add documents to Qdrant", "details": str(e)}
