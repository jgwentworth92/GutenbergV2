import pytest
from unittest import mock
from icecream import ic


from models import constants
from services.github_service import fetch_and_emit_commits
from services.message_processing_service import process_messages
from services.vectordb_service import process_message_to_vectordb


# Test for the github_listener_dataflow
@mock.patch('services.user_management_service.user_management_service.update_status')
def test_github_commits_hello_world(mock_update_status, create_dataflow, run_dataflow, sample_repo_info_1):
    flow, captured_output = create_dataflow(fetch_and_emit_commits, sample_repo_info_1)
    run_dataflow(flow)

    mock_update_status.assert_any_call(
        constants.Service.GITHUB_SERVICE,
        sample_repo_info_1['job_id'],
        constants.StepStatus.COMPLETE.value,
    )

    for data in captured_output:
        if "commit_id" in data[0]:
            rtn=data[0]
            assert "page_content" in data[0]
            assert "metadata" in rtn
            assert "filename" in rtn["metadata"]
            assert "status" in rtn["metadata"]
            assert "additions" in rtn["metadata"]
            assert "deletions" in rtn["metadata"]
            assert "changes" in rtn["metadata"]
            assert "author" in rtn["metadata"]
            assert "date" in rtn["metadata"]
            assert "repo_name" in rtn["metadata"]
            assert "commit_url" in rtn["metadata"]
            assert "id" in data["metadata"]
            assert "token_count" in rtn["metadata"]


@mock.patch('services.user_management_service.user_management_service.update_status')
def test_github_commits_invalid_repo(mock_update_status, create_dataflow, run_dataflow, invalid_repo_info):
    flow, captured_output = create_dataflow(fetch_and_emit_commits, invalid_repo_info)
    run_dataflow(flow)
    mock_update_status.assert_any_call(
        constants.Service.GITHUB_SERVICE,
        invalid_repo_info['job_id'],
        constants.StepStatus.FAILED.value,
    )
    for data in captured_output:
        assert "error" in data
        assert "details" in data
        assert "yo mama" in data
        assert "repo" in data or "commit_id" in data


# Additional Tests for commit_summary_service_dataflow using fake event data
def test_commit_summary(create_dataflow, run_dataflow, fake_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_messages(msg), fake_event_data)
    run_dataflow(flow)

    ic(captured_output)
    assert len(captured_output) > 0  # Ensure some output is captured

    for data in captured_output:
        if "commit_id" in data[0]:
            rtn=data[0]
            assert "page_content" in data[0]
            assert "metadata" in rtn
            assert "filename" in rtn["metadata"]
            assert "status" in rtn["metadata"]
            assert "additions" in rtn["metadata"]
            assert "deletions" in rtn["metadata"]
            assert "changes" in rtn["metadata"]
            assert "author" in rtn["metadata"]
            assert "date" in rtn["metadata"]
            assert "repo_name" in rtn["metadata"]
            assert "commit_url" in rtn["metadata"]
            assert "id" in data["metadata"]
            assert "token_count" in rtn["metadata"]


def test_error_message_handling(create_dataflow, run_dataflow, error_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_messages(msg), error_event_data)
    run_dataflow(flow)

    ic(captured_output)
    assert len(captured_output) == 0  # Ensure no output is captured for error messages


# Test for malformed repo data


def test_malformed_document_processing(create_dataflow, run_dataflow, malformed_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_messages(msg), malformed_event_data)
    run_dataflow(flow)

    ic(captured_output)

    for data in captured_output:
        assert "error" in data
        if "error" in data:
            assert "error" in data
            assert "details" in data
            assert "event_data" in data
            assert data['error'] == "Failed to create documents"


def test_qdrant(create_dataflow, run_dataflow,fake_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_message_to_vectordb(msg), fake_event_data)
    run_dataflow(flow)

    ic(f"captured data:{captured_output}")
    for msg in captured_output:
        ic(f"looped captured data {msg}")
        assert "id" in msg
        assert "collection_name" in msg
        assert msg["collection_name"] == "Hello-World"
        assert msg["id"]==["8996e7f9-4ea3-1fd2-3d59-55d74de62da4"]
    assert len(captured_output) > 0
