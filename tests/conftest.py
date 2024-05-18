import pytest
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.testing import TestingSource, TestingSink,run_main
import logging

from kafkaGithubConsumer.githubConsumer import fetch_and_emit_commits

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture
def sample_repo_info_1():
    return {"owner": "octocat", "repo_name": "Hello-World"}


@pytest.fixture
def sample_repo_info_2():
    return {"owner": "octocat", "repo_name": "Spoon-Knife"}


@pytest.fixture
def invalid_repo_info():
    return {"owner": "invalid", "repo_name": "invalid-repo"}


@pytest.fixture
def dataflow():
    def _create_dataflow(repo_info):
        logger.debug(f"Creating dataflow for repo: {repo_info['repo_name']}")

        # Create the dataflow with a unique name based on the repository
        flow = Dataflow(f"Github_Repo_Test_{repo_info['repo_name']}")

        # Define the input source using the provided repository information
        inp = op.input("inp", flow, TestingSource([repo_info]))

        # Inspect the input for debugging purposes
        op.inspect("check_inp", inp)

        # Map the input to fetch and emit commits
        commits = op.flat_map("fetch_and_emit_commits", inp, fetch_and_emit_commits)

        # Inspect the emitted commits for debugging purposes
        op.inspect("check_commits", commits)

        # Capture the output using TestingSink
        captured_output = []
        op.output("capture_output", commits, TestingSink(captured_output))

        # Return the flow and the list to capture output
        return flow, captured_output

    return _create_dataflow


@pytest.fixture
def run_test():
    def _run_test(flow, captured_output):
        """
        Run the dataflow and perform assertions on the captured output.

        Parameters:
        flow: Dataflow instance to run.
        captured_output: List to capture output data.
        """
        logger.info("Running dataflow")

        # Run the dataflow
        run_main(flow)

        # Log the captured output
        for data in captured_output:
            if "commit_id" in data:
                logger.debug(f"Commit data: {data}")
                assert "author" in data
                assert "message" in data
                assert "date" in data
                assert "url" in data
                assert "repo_name" in data
                assert "commit_id" in data
                assert "files" in data
            elif "error" in data:
                logger.error(f"Error data: {data}")
                assert "error" in data
                assert "details" in data
                assert "repo" in data or "commit_id" in data

    return _run_test
