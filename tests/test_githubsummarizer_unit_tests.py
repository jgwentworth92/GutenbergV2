import pytest
from icecream import ic

from services.github_service import fetch_and_emit_commits
from services.message_processing_service import process_message


# Test for the github_listener_dataflow
def test_github_commits_hello_world(create_dataflow, run_dataflow, sample_repo_info_1):
    flow, captured_output = create_dataflow(fetch_and_emit_commits, sample_repo_info_1)
    run_dataflow(flow)

    for data in captured_output:
        assert "commit_id" in data
        assert "author" in data
        assert "message" in data
        assert "date" in data
        assert "url" in data
        assert "repo_name" in data
        assert "files" in data

def test_github_commits_invalid_repo(create_dataflow, run_dataflow, invalid_repo_info):
    flow, captured_output = create_dataflow(fetch_and_emit_commits, invalid_repo_info)
    run_dataflow(flow)

    for data in captured_output:
        assert "error" in data
        assert "details" in data
        assert "repo" in data or "commit_id" in data

# Additional Tests for commit_summary_service_dataflow using fake event data
def test_commit_summary(create_dataflow,  run_dataflow,fake_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_message(msg), fake_event_data)
    run_dataflow(flow)

    ic(captured_output)
    assert len(captured_output) > 0  # Ensure some output is captured

    for data in captured_output:
        if "commit_id" in data:
            assert "page_content" in data
            assert "metadata" in data
            assert "filename" in data["metadata"]
            assert "status" in data["metadata"]
            assert "additions" in data["metadata"]
            assert "deletions" in data["metadata"]
            assert "changes" in data["metadata"]
            assert "author" in data["metadata"]
            assert "date" in data["metadata"]
            assert "repo_name" in data["metadata"]
            assert "commit_url" in data["metadata"]
            assert "id" in data["metadata"]
            assert "token_count" in data["metadata"]

def test_error_message_handling(create_dataflow, run_dataflow, error_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_message(msg), error_event_data)
    run_dataflow(flow)

    ic(captured_output)
    assert len(captured_output) == 0  # Ensure no output is captured for error messages

# Test for malformed repo data
def test_malformed_document_create(create_dataflow, run_dataflow, malformed_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_message(msg), malformed_event_data)
    run_dataflow(flow)

    ic(captured_output)
    assert len(captured_output) > 0  # Ensure some output is captured

    for data in captured_output:
        if "error" in data:
            assert "error" in data
            assert "details" in data
            assert "event_data" in data
            assert data['error'] == "Failed to create documents"

def test_malformed_document_processing(create_dataflow, run_dataflow, document_processing_error_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_message(msg), document_processing_error_event_data)
    run_dataflow(flow)

    ic(captured_output)
    assert len(captured_output) > 0  # Ensure some output is captured

    for data in captured_output:
        if "error" in data:
            assert "error" in data
            assert "details" in data
            assert "event_data" in data
            assert data['error'] == "Failed to process document"