import pytest
import json
from models.document import Document
from utils.status_update import StandardizedMessage
from services.message_processing_service import prepare_batch_inputs, process_raw_data_with_llm

def test_prepare_batch_inputs(sample_documents):
    result = prepare_batch_inputs(sample_documents)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert "text" in result[0]
    assert result[0]["text"].startswith("Filename: README, Status: added")

def test_process_raw_data_with_llm_success(fake_event_data, standard_message_factory):
    input_message = standard_message_factory(
        job_id="1502f682-a81d-4dfc-9c8b-fd1e2ad829f2",
        step_number=1,
        data=fake_event_data
    )
    results = list(process_raw_data_with_llm(input_message))

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, StandardizedMessage)
    assert result.job_id == "1502f682-a81d-4dfc-9c8b-fd1e2ad829f2"
    assert result.step_number == 1
    assert isinstance(result.data, list)
    assert len(result.data) == 2  # Original document and summary

    original_doc = json.loads(result.data[0])
    summary_doc = json.loads(result.data[1])

    assert original_doc['page_content'].startswith("Filename: README, Status: added")
    assert summary_doc['page_content'].startswith("Summary: ")
    assert summary_doc['metadata']['vector_id'].endswith('_llm')
    assert summary_doc['metadata']['job_id'] == "1502f682-a81d-4dfc-9c8b-fd1e2ad829f2"
    assert summary_doc['metadata']['repo_name'] == "Hello-World"
    assert summary_doc['metadata']['doc_type'] == "SUMMARY"

    assert "document_count" in result.metadata

def test_process_raw_data_with_llm_empty_input(standard_message_factory):
    input_message = standard_message_factory(
        job_id="test_job",
        step_number=1,
        data=[]
    )
    results = list(process_raw_data_with_llm(input_message))
    assert len(results) == 0

def test_process_raw_data_with_llm_invalid_input(standard_message_factory):
    invalid_messages = ['{"invalid": "json"}', 'not json at all']
    input_message = standard_message_factory(
        job_id="test_job",
        step_number=1,
        data=invalid_messages
    )
    results = list(process_raw_data_with_llm(input_message))
    assert len(results) == 0  # No results should be produced for invalid input

def test_process_raw_data_with_llm_exception_handling(standard_message_factory):
    invalid_messages = ["{\"page_content\":\"\",\"metadata\":{},\"type\":\"Document\"}"]
    input_message = standard_message_factory(
        job_id="test_job",
        step_number=1,
        data=invalid_messages
    )
    results = list(process_raw_data_with_llm(input_message))
    assert len(results) == 0  # Should still process empty documents

def test_process_raw_data_with_llm_batch_processing(fake_event_data, standard_message_factory):
    # Duplicate the fake event data to test batch processing
    batch_data = fake_event_data * 2
    input_message = standard_message_factory(
        job_id="test_job",
        step_number=1,
        data=batch_data
    )
    results = list(process_raw_data_with_llm(input_message))
    assert len(results) == 1
    result = results[0]
    assert isinstance(result, StandardizedMessage)
    assert len(result.data) == 4  # 2 original documents and 2 summaries
    for i in range(0, len(result.data), 2):
        original_doc = json.loads(result.data[i])
        summary_doc = json.loads(result.data[i+1])
        assert original_doc['page_content'].startswith("Filename: README, Status: added")
        assert summary_doc['page_content'].startswith("Summary: ")
        assert summary_doc['metadata']['vector_id'].endswith('_llm')
        assert summary_doc['metadata']['doc_type'] == "SUMMARY"