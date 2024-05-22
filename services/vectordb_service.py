import logging
from typing import Generator, Dict, Any

from icecream import ic
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from config.config_setting import config
from utils.get_qdrant import get_qdrant_vector_store


def process_message_to_vectordb(message: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    ic(message)

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

    for doc in documents:
        logging.info(f"metadata of commit {doc.metadata}")
        logging.info(f"page content of commit {doc.page_content}")

    # Determine collection name dynamically from document metadata
    collection_name = documents[0].metadata.get('author') + "_" + str(documents[0].metadata.get('repo_name'))
    logging.info(f"Collection is called {collection_name}")

    try:
        embed = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
        vectordb = get_qdrant_vector_store(host=config.VECTOR_DB_HOST, port=config.VECTOR_DB_PORT,
                                           embeddings=embed, collection_name=collection_name)
        ids = vectordb.add_documents(documents)
        result_message = {collection_name: ids}
        logging.info(f"Processed {len(ids)} documents into vectordb collection")
        yield result_message
    except Exception as e:
        logging.error(f"Failed to add documents to Qdrant: {e}")
        yield {"error": "Failed to add documents to Qdrant", "details": str(e)}