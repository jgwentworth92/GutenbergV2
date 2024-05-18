import logging
import pytest

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_github_commits_hello_world(dataflow, sample_repo_info_1, run_test):
    """
    Test fetching and emitting commits for the Hello-World repository.
    """
    logger.info("Starting test for Hello-World repository")
    flow, captured_output = dataflow(sample_repo_info_1)
    run_test(flow, captured_output)

def test_github_commits_spoon_knife(dataflow, sample_repo_info_2, run_test):
    """
    Test fetching and emitting commits for the Spoon-Knife repository.
    """
    logger.info("Starting test for Spoon-Knife repository")
    flow, captured_output = dataflow(sample_repo_info_2)
    run_test(flow, captured_output)

def test_github_commits_invalid_repo(dataflow, invalid_repo_info, run_test):
    """
    Test fetching and emitting commits for an invalid repository.
    """
    logger.info("Starting test for invalid repository")
    flow, captured_output = dataflow(invalid_repo_info)
    run_test(flow, captured_output)

