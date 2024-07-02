
import pytest
from github import Github, Auth
import orjson

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

# Test for the github_listener_dataflow
def test_github_commits_hello_world(create_dataflow, run_dataflow, sample_repo_info_1):
    flow, captured_output = create_dataflow(fetch_and_emit_commits, sample_repo_info_1)
    run_dataflow(flow)

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


def test_github_commits_invalid_repo(create_dataflow, run_dataflow, invalid_repo_info):
    flow, captured_output = create_dataflow(fetch_and_emit_commits, invalid_repo_info)
    run_dataflow(flow)
    for data in captured_output:
        assert "error" in data
        assert "details" in data
        assert "repo" in data or "commit_id" in data


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

def test_fetch_and_emit_commits():
    resource_data = {
        "resource_data": orjson.dumps({"owner": "octocat", "repo_name": "Hello-World"}),
        "job_id": "test_job_456"
    }
    documents = list(fetch_and_emit_commits(resource_data))
    assert len(documents) > 0
    for doc in documents:
        assert isinstance(doc, str)
        parsed_doc = orjson.loads(doc)
        assert "page_content" in parsed_doc
        assert "metadata" in parsed_doc
        assert parsed_doc["metadata"]["job_id"] == "test_job_456"