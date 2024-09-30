import pytest
from github import Github, Auth
import orjson

from logging_config import get_logger, setup_logging
from services.github_service import (
    fetch_repository,
    create_document,
    fetch_commit_data,
    fetch_all_commit_data,
    get_latest_files,
    create_documents,
    fetch_and_emit_commits,
)
from models.commit import CommitData, FileInfo
from models.document import Document
from config.config_setting import config
from utils.status_update import StandardizedMessage


setup_logging()
logger = get_logger(__name__)


def test_github_commits_hello_world(create_dataflow, run_dataflow, sample_repo_info_1, standard_message_factory):
    # Correctly structure the input data
    resource_data = orjson.loads(sample_repo_info_1['resource_data'])
    input_message = standard_message_factory(
        job_id=sample_repo_info_1['job_id'],
        step_number=1,
        data={

                "resource_data": orjson.dumps(resource_data).decode('utf-8')
        }
    )

    logger.info(f"Input message: {input_message}")

    flow, captured_output = create_dataflow(fetch_and_emit_commits, input_message)
    run_dataflow(flow)

    logger.info(f"Captured output: {captured_output}")

    assert len(captured_output) > 0, f"Expected output from fetch_and_emit_commits, got {captured_output}"

    for output in captured_output:
        assert isinstance(output, StandardizedMessage), f"Expected StandardizedMessage, got {type(output)}"
        assert output.job_id == sample_repo_info_1['job_id'], f"Expected job_id {sample_repo_info_1['job_id']}, got {output.job_id}"
        assert output.step_number == 1, f"Expected step_number 1, got {output.step_number}"
        assert isinstance(output.data, list), f"Expected list, got {type(output.data)}"
        for doc in output.data:
            parsed_doc = orjson.loads(doc)
            assert "page_content" in parsed_doc, f"Missing 'page_content' in {parsed_doc}"
            assert "metadata" in parsed_doc, f"Missing 'metadata' in {parsed_doc}"
            metadata = parsed_doc["metadata"]
            expected_keys = [
                "filename", "status", "additions", "deletions", "changes",
                "author", "date", "repo_name", "commit_url", "id", "job_id",
                "token_count", "collection_name", "vector_id"
            ]
            for key in expected_keys:
                assert key in metadata, f"Missing '{key}' in metadata: {metadata}"
        assert "repo_name" in output.metadata, f"Missing 'repo_name' in metadata: {output.metadata}"
        assert "document_count" in output.metadata, f"Missing 'document_count' in metadata: {output.metadata}"

# ... [other tests remain unchanged] ...

def test_github_commits_invalid_repo(create_dataflow, run_dataflow, invalid_repo_info, standard_message_factory):
    input_message = standard_message_factory(
        job_id="1502f682-a81d-4dfc-9c8b-fd1e2ad829f2",
        step_number=1,
        data={"data": {"resource_data": orjson.dumps(invalid_repo_info).decode('utf-8')}}
    )
    flow, captured_output = create_dataflow(fetch_and_emit_commits, input_message)
    run_dataflow(flow)

    assert len(captured_output) == 0  # Expecting no output for invalid repo


def test_fetch_repository():
    owner = "octocat"
    repo_name = "Hello-World"
    repo = fetch_repository(owner, repo_name)
    assert repo is not None
    assert repo.full_name == f"{owner}/{repo_name}"


def test_create_document():
    file_info = FileInfo(
        filename="README.md",
        status="modified",
        additions=1,
        deletions=1,
        changes=2,
        patch="@@ -1,3 +1,3 @@\n-# Hello World\n+# Hello GitHub\n \n This is a test repo."
    )
    event_data = CommitData(
        author="Test User",
        message="Update README",
        date="2023-06-28T12:00:00Z",
        url="https://github.com/test/repo/commit/123456",
        repo_name="test/repo",
        commit_id="123456",
        files=[file_info]
    )
    job_id = "test_job_123"

    document = create_document(file_info, event_data, job_id)
    assert isinstance(document, Document)
    assert document.page_content.startswith("Filename: README.md")
    assert document.metadata["job_id"] == job_id


def test_fetch_commit_data(github_client):
    repo = github_client.get_repo("octocat/Hello-World")
    commit = repo.get_commits()[0]
    commit_data = fetch_commit_data((commit, repo.name))
    assert isinstance(commit_data, CommitData)
    assert commit_data.repo_name == repo.name
    assert commit_data.commit_id == commit.sha


@pytest.mark.parametrize("repo_name", [("octocat/Hello-World"), ("pytorch/pytorch")])
def test_fetch_all_commit_data(github_client, repo_name):
    repo = github_client.get_repo(repo_name)
    commits = list(repo.get_commits()[:5])  # Convert to list and limit to 5 commits for testing
    all_commit_data = fetch_all_commit_data(commits, repo.name)
    assert len(all_commit_data) == len(commits)
    assert all(isinstance(cd, CommitData) for cd in all_commit_data)


def test_get_latest_files():
    commit_data_1 = CommitData(
        author="User1",
        message="Commit 1",
        date="2023-06-27T12:00:00Z",
        url="https://github.com/test/repo/commit/111",
        repo_name="test/repo",
        commit_id="111",
        files=[FileInfo(filename="file1.txt", status="modified", additions=1, deletions=0, changes=1, patch="patch1")]
    )
    commit_data_2 = CommitData(
        author="User2",
        message="Commit 2",
        date="2023-06-28T12:00:00Z",
        url="https://github.com/test/repo/commit/222",
        repo_name="test/repo",
        commit_id="222",
        files=[FileInfo(filename="file1.txt", status="modified", additions=1, deletions=1, changes=2, patch="patch2")]
    )
    all_commit_data = [commit_data_1, commit_data_2]
    latest_files = get_latest_files(all_commit_data)
    assert len(latest_files) == 1
    assert latest_files["file1.txt"]["commit_id"] == "222"


def test_create_documents():
    file_info = FileInfo(
        filename="README.md",
        status="modified",
        additions=1,
        deletions=1,
        changes=2,
        patch="@@ -1,3 +1,3 @@\n-# Hello World\n+# Hello GitHub\n \n This is a test repo."
    )
    commit_data = CommitData(
        author="Test User",
        message="Update README",
        date="2023-06-28T12:00:00Z",
        url="https://github.com/test/repo/commit/123456",
        repo_name="test/repo",
        commit_id="123456",
        files=[file_info]
    )
    latest_files = {"README.md": {"file": file_info, "commit_id": "123456", "date": "2023-06-28T12:00:00Z"}}
    all_commit_data = [commit_data]
    job_id = "test_job_123"

    documents = create_documents(latest_files, all_commit_data, job_id)
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].metadata["job_id"] == job_id

