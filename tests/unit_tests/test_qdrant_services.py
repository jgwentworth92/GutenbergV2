import pytest
from unittest.mock import patch, MagicMock
from models.document import Document
from services.vectordb_service import process_message_to_vectordb
from utils.status_update import StandardizedMessage
from logging_config import get_logger

logger = get_logger(__name__)



def test_process_message_to_vectordb_success(mock_get_qdrant, mock_setup_embedding, sample_standardized_message, mock_qdrant_instance):
    logger.info("Starting test_process_message_to_vectordb_success")
    result = list(process_message_to_vectordb(sample_standardized_message))

    logger.info(f"Result: {result}")
    assert len(result) == 1
    assert result[0] == {
        "collection_name": "test_collection",
        "vector_db_id": "ee21dd38-8b8c-8c73-8493-8dea245afcc2",  # MD5 hash of "test_vector_id"
        "job_id": "test_job_id",
        "document_type": "TEST_TYPE"
    }

    logger.info("Asserting mock calls")
    mock_get_qdrant.assert_called_once()
    mock_qdrant_instance.add_texts.assert_called_once()
    args, kwargs = mock_qdrant_instance.add_texts.call_args
    logger.debug(f"add_texts called with args: {args}, kwargs: {kwargs}")
    assert kwargs['texts'] == ["Test content"]
    assert kwargs['metadatas'][0]['collection_name'] == "test_collection"
    assert kwargs['metadatas'][0]['job_id'] == "test_job_id"
    assert kwargs['metadatas'][0]['vector_id'] == "test_vector_id"
    assert kwargs['ids'] == ["ee21dd38-8b8c-8c73-8493-8dea245afcc2"]
    logger.info("test_process_message_to_vectordb_success completed successfully")

def test_process_message_to_vectordb_invalid_json(sample_standardized_message):
    logger.info("Starting test_process_message_to_vectordb_invalid_json")
    sample_standardized_message.data = ["invalid json"]
    result = list(process_message_to_vectordb(sample_standardized_message))
    logger.info(f"Result: {result}")
    assert len(result) == 0
    logger.info("test_process_message_to_vectordb_invalid_json completed successfully")

def test_process_message_to_vectordb_qdrant_error(mock_get_qdrant, mock_setup_embedding, sample_standardized_message, mock_qdrant_instance):
    logger.info("Starting test_process_message_to_vectordb_qdrant_error")
    mock_qdrant_instance.add_texts.side_effect = Exception("Qdrant error")
    result = list(process_message_to_vectordb(sample_standardized_message))
    logger.info(f"Result: {result}")
    assert len(result) == 0
    logger.info("test_process_message_to_vectordb_qdrant_error completed successfully")
