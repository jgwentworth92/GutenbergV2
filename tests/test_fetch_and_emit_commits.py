import logging

import pytest
from bytewax.testing import run_main
from icecream import ic

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
def run_test(dataflow, repo_info):
    """
    Run the dataflow and perform assertions on the captured output.

    Parameters:
    dataflow: tuple containing the Dataflow instance and the list to capture output.
    repo_info: dictionary containing repository information.
    """
    flow, captured_output = dataflow

    # Run the dataflow
    run_main(flow)

    # Assertions to verify the captured output
    for data in captured_output:
        ic(f"commit info: {data}")
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

    ic(f"All assertions passed for repo: {repo_info['repo_name']}")
    ic(f"Captured output for repo {repo_info['repo_name']}: {captured_output}")

def test_github_commits_hello_world(sample_repo_info_1):
    """
    Test fetching and emitting commits for the Hello-World repository.
    """
    run_test(sample_repo_info_1, "Hello-World")

def test_github_commits_spoon_knife(sample_repo_info_2):
    """
    Test fetching and emitting commits for the Spoon-Knife repository.
    """
    run_test(sample_repo_info_2, "Spoon-Knife")

def test_github_commits_invalid_repo(invalid_repo_info):
    """
    Test fetching and emitting commits for an invalid repository.
    """
    run_test(invalid_repo_info, "invalid-repo")

if __name__ == "__main__":
    pytest.main()
