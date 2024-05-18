import pytest
from bytewax.dataflow import Dataflow
from bytewax.testing import TestingSource, TestingSink, run_main
from kafkaGithubConsumer.githubConsumer import fetch_and_emit_commits
import bytewax.operators as op

# Fixture providing mock repository information for the Hello-World repository
@pytest.fixture
def sample_repo_info_1():
    return {"owner": "octocat", "repo_name": "Hello-World"}

# Fixture providing mock repository information for the Spoon-Knife repository
@pytest.fixture
def sample_repo_info_2():
    return {"owner": "octocat", "repo_name": "Spoon-Knife"}

# Fixture providing invalid repository information
@pytest.fixture
def invalid_repo_info():
    return {"owner": "invalid", "repo_name": "invalid-repo"}

# Fixture that sets up the dataflow for the given repository information
@pytest.fixture
def dataflow(repo_info):
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
