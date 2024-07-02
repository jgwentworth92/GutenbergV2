import pytest
from unittest.mock import patch, MagicMock
from services.vectordb_service import process_message_to_vectordb, generate_uuid_from_string
from models.document import Document
import json




def test_process_message_to_vectordb_empty_input():
    results = list(process_message_to_vectordb([]))
    assert len(results) == 0


def test_process_message_to_vectordb_invalid_input():
    invalid_input = ["invalid json"]
    results = list(process_message_to_vectordb(invalid_input))
    assert len(results) == 0


@patch('services.vectordb_service.get_qdrant_vector_store')
def test_process_message_to_vectordb_exception(mock_get_qdrant, qdrant_event_data, mock_embedding):
    mock_get_qdrant.side_effect = Exception("Test exception")
    results = list(process_message_to_vectordb(qdrant_event_data))
    assert len(results) == 0


def test_generate_uuid_from_string():
    test_string = "test_string"
    uuid = generate_uuid_from_string(test_string)
    assert uuid.hex == "3474851a3410906697ec77337df7aae4"


@patch('services.vectordb_service.get_qdrant_vector_store')
def test_process_message_to_vectordb_success(mock_get_qdrant, qdrant_event_data, mock_embedding):
    mock_qdrant = MagicMock()
    mock_qdrant.add_texts.return_value = ["8996e7f9-4ea3-1fd2-3d59-55d74de62da4"]
    mock_get_qdrant.return_value = mock_qdrant

    results = list(process_message_to_vectordb(qdrant_event_data))

    assert len(results) == 1
    assert "collection_name" in results[0]
    assert "vector_db_id" in results[0]
    assert "job_id" in results[0]
    assert results[0]["collection_name"] == "Hello-World"
    assert results[0]["vector_db_id"] == "8996e7f9-4ea3-1fd2-3d59-55d74de62da4"  # Changed this line
    assert results[0]["job_id"] == "1502f682-a81d-4dfc-9c8b-fd1e2ad829f2"


@patch('services.vectordb_service.get_qdrant_vector_store')
def test_process_message_to_vectordb_multiple_documents(mock_get_qdrant, mock_embedding):
    multiple_docs = [
        json.dumps(Document(page_content="Doc 1",
                            metadata={"collection_name": "Test", "job_id": "job1", "vector_id": "id1"}).dict()),
        json.dumps(Document(page_content="Doc 2",
                            metadata={"collection_name": "Test", "job_id": "job1", "vector_id": "id2"}).dict())
    ]
    mock_qdrant = MagicMock()
    mock_qdrant.add_texts.return_value = ["uuid1", "uuid2"]
    mock_get_qdrant.return_value = mock_qdrant

    results = list(process_message_to_vectordb(multiple_docs))

    assert len(results) == 2
    assert all("collection_name" in result for result in results)
    assert all("vector_db_id" in result for result in results)
    assert all("job_id" in result for result in results)
    assert all(result["collection_name"] == "Test" for result in results)
    assert results[0]["vector_db_id"] == "uuid1"  # Changed this line
    assert results[1]["vector_db_id"] == "uuid2"  # Changed this line


@patch('services.vectordb_service.get_qdrant_vector_store')
@patch('services.vectordb_service.config')
def test_process_message_to_vectordb_existing_collection(mock_config, mock_get_qdrant, qdrant_event_data, mock_embedding):
    mock_qdrant = MagicMock()
    mock_qdrant.add_texts.return_value = ["8996e7f9-4ea3-1fd2-3d59-55d74de62da4"]
    mock_get_qdrant.return_value = mock_qdrant
    mock_config.VECTOR_DB_HOST = "test_host"
    mock_config.VECTOR_DB_PORT = 1234

    results = list(process_message_to_vectordb(qdrant_event_data))

    assert len(results) == 1
    mock_get_qdrant.assert_called_once()