import pytest
import json
from models.document import Document
from services.message_processing_service import prepare_batch_inputs, process_messages


def test_prepare_batch_inputs(sample_documents):
    result = prepare_batch_inputs(sample_documents)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert "text" in result[0]
    assert result[0]["text"].startswith("Filename: README, Status: added")

def test_process_messages_success(fake_event_data):
    results = list(process_messages(fake_event_data))

    assert len(results) == 1
    result = json.loads(results[0])
    assert result['page_content'].startswith("Summary: ")
    assert 'metadata' in result
    assert result['metadata']['vector_id'].endswith('_llm')
    assert result['metadata']['job_id'] == "1502f682-a81d-4dfc-9c8b-fd1e2ad829f2"
    assert result['metadata']['repo_name'] == "Hello-World"

def test_process_messages_empty_input():
    results = list(process_messages([]))
    assert len(results) == 0

def test_process_messages_invalid_input():
    invalid_messages = ['{"invalid": "json"}', 'not json at all']
    results = list(process_messages(invalid_messages))
    assert len(results) == 0  # No results should be produced for invalid input

def test_process_messages_exception_handling():
    invalid_messages = ["{\"page_content\":\"\",\"metadata\":{},\"type\":\"Document\"}"]
    results = list(process_messages(invalid_messages))
    assert len(results) == 0  # Should still process empty documents



def test_process_messages_batch_processing(fake_event_data):
    # Duplicate the fake event data to test batch processing
    batch_data = fake_event_data * 2
    results = list(process_messages(batch_data))
    assert len(results) == 2
    for result in results:
        parsed_result = json.loads(result)
        assert parsed_result['page_content'].startswith("Summary: ")
        assert parsed_result['metadata']['vector_id'].endswith('_llm')