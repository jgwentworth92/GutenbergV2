
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

def process_message_to_vectordb(message: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:


    if "error" in message:
        logging.error(f"Error in message: {message}")
        yield {"error": "Invalid message received", "details": message}
        return

    if not message:
        logging.error("Received an empty message")
        yield {"error": "Received an empty message"}
        return

    try:
        documents = [Document(page_content=message['page_content'], metadata=message['metadata'])]
    except Exception as e:
        logging.error(f"Failed to parse documents: {e}")
        yield {"error": "Failed to parse documents", "details": str(e)}
        return

    if not documents:
        logging.error("No valid documents found in the message")
        yield {"error": "No valid documents found", "details": message}
        return




    collection_name = documents[0].metadata.get('collection_name')
    logging.info(f"Collection is called {collection_name}")

    try:
        embed = setup_embedding_model()
        vectordb = get_qdrant_vector_store(host=config.VECTOR_DB_HOST, port=config.VECTOR_DB_PORT,
                                           embeddings=embed, collection_name=collection_name)
        ids = vectordb.add_documents(documents)
        result_message = {"collection_name":collection_name,"id":ids}
        logging.info(f"Processed {len(ids)} documents into vectordb collection")
        yield result_message
    except Exception as e:
        logging.error(f"Failed to add documents to Qdrant: {e}")
        yield {"error": "Failed to add documents to Qdrant", "details": str(e)}