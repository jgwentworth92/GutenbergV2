import pytest
from bytewax.testing import run_main

def run_test(flow, captured_output):
    """
    Run the dataflow and perform assertions on the captured output.

    Parameters:
    flow: Dataflow instance to run.
    captured_output: List to capture output data.
    """
    # Run the dataflow
    run_main(flow)

    # Log the captured output
    for data in captured_output:
        if "commit_id" in data:
            assert "author" in data
            assert "message" in data
            assert "date" in data
            assert "url" in data
            assert "repo_name" in data
            assert "commit_id" in data
            assert "files" in data
        elif "error" in data:
            assert "error" in data
            assert "details" in data
            assert "repo" in data or "commit_id" in data

def test_github_commits_hello_world(dataflow, sample_repo_info_1):
    """
    Test fetching and emitting commits for the Hello-World repository.
    """
    flow, captured_output = dataflow(sample_repo_info_1)
    run_test(flow, captured_output)

def test_github_commits_spoon_knife(dataflow, sample_repo_info_2):
    """
    Test fetching and emitting commits for the Spoon-Knife repository.
    """
    flow, captured_output = dataflow(sample_repo_info_2)
    run_test(flow, captured_output)

def test_github_commits_invalid_repo(dataflow, invalid_repo_info):
    """
    Test fetching and emitting commits for an invalid repository.
    """
    flow, captured_output = dataflow(invalid_repo_info)
    run_test(flow, captured_output)

if __name__ == "__main__":
    pytest.main()
