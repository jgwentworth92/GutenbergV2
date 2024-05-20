import pytest
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.testing import TestingSource, TestingSink, run_main
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Sample Fixtures for Repo Information
@pytest.fixture
def sample_repo_info_1():
    return {"owner": "octocat", "repo_name": "Hello-World"}


@pytest.fixture
def sample_repo_info_2():
    return {"owner": "octocat", "repo_name": "Spoon-Knife"}


@pytest.fixture
def invalid_repo_info():
    return {"owner": "invalid", "repo_name": "invalid-repo"}


# Fake Event Data Fixture
@pytest.fixture
def fake_event_data():
    return {
        "author": "The Octocat",
        "message": "Create styles.css and updated README",
        "date": "2014-02-04T22:38:36+00:00",
        "url": "https://github.com/octocat/Spoon-Knife/commit/bb4cc8d3b2e14b3af5df699876dd4ff3acd00b7f",
        "repo_name": "Goood_Event_Data",
        "commit_id": "bb4cc8d3b2e14b3af5df699876dd4ff3acd00b7f",
        "files": [
            {
                "filename": "README.md",
                "status": "added",
                "additions": 9,
                "deletions": 0,
                "changes": 9,
                "patch": "@@ -0,0 +1,9 @@\n+### Well hello there!\n+\n+This repository is meant to provide an example for *forking* a repository on GitHub.\n+\n+Creating a *fork* is producing a personal copy of someone else's project. Forks act as a sort of bridge between the original repository and your personal copy. You can submit *Pull Requests* to help make other people's projects better by offering your changes up to the original project. Forking is at the core of social coding at GitHub.\n+\n+After forking this repository, you can make some changes to the project, and submit [a Pull Request](https://github.com/octocat/Spoon-Knife/pulls) as practice.\n+\n+For some more information on how to fork a repository, [check out our guide, \"Fork a Repo\"](https://help.github.com/articles/fork-a-repo). Thanks! :sparkling_heart:"
            },
            {
                "filename": "styles.css",
                "status": "added",
                "additions": 17,
                "deletions": 0,
                "changes": 17,
                "patch": "@@ -0,0 +1,17 @@\n+* {\n+  margin:0px;\n+  padding:0px;\n+}\n+\n+#octocat {\n+  display: block;\n+  width:384px;\n+  margin: 50px auto;\n+}\n+\n+p {\n+  display: block;\n+  width: 400px;\n+  margin: 50px auto;\n+  font: 30px Monaco,\"Courier New\",\"DejaVu Sans Mono\",\"Bitstream Vera Sans Mono\",monospace;\n+}"
            }
        ]
    }



# Generalized Fixture to Create Dataflows
@pytest.fixture
def create_dataflow():
    def _create_dataflow(processing_function, input_data):
        logger.debug(f"Creating dataflow")

        flow = Dataflow(f"Test_Dataflow")

        inp = op.input("inp", flow, TestingSource([input_data]))
        op.inspect("check_inp", inp)

        # Ensure processing_function is applied with flat_map
        processed = op.flat_map("process", inp, processing_function)

        op.inspect("check_processed", processed)

        captured_output = []
        op.output("capture_output", processed, TestingSink(captured_output))

        return flow, captured_output

    return _create_dataflow

# Generalized Fixture to Run Dataflows
@pytest.fixture
def run_dataflow():
    def _run_dataflow(flow):
        logger.info("Running dataflow")

        run_main(flow)

    return _run_dataflow
@pytest.fixture
def error_event_data():
    return {
        "error": "Failed to fetch repository",
        "details": "404 {\"message\": \"Not Found\", \"documentation_url\": \"https://docs.github.com/rest/repos/repos#get-a-repository\"}",
        "repo": "jgwentworth92/Gutenberg-Ingestion-Pipeline"
    }

@pytest.fixture
def malformed_event_data():
    return {
        "message": "Create styles.css and updated README",
        "date": "2014-02-04T22:38:36+00:00",
        "url": "https://github.com/octocat/Spoon-Knife/commit/bb4cc8d3b2e14b3af5df699876dd4ff3acd00b7f",
        "repo_name": "Spoon-Knife",
        "commit_id": "bb4cc8d3b2e14b3af5df699876dd4ff3acd00b7f",
        "files": [
            {
                "filename": "README.md",
                "status": "added",
                "additions": 9,
                "deletions": 0,
                "changes": 9

            },
            {
                "filename": "styles.css",
                "status": "added",
                "additions": 17,
                "deletions": 0,
                "changes": 17

            }
        ]
    }


@pytest.fixture
def document_processing_error_event_data():
    return {
        "author": "The Octocat",
        "message": "Create styles.css and updated README",
        "date": "2014-02-04T22:38:36+00:00",
        "url": "https://github.com/octocat/Spoon-Knife/commit/bb4cc8d3b2e14b3af5df699876dd4ff3acd00b7f",
        "repo_name": "Spoon-Knife",
        "commit_id": "bb4cc8d3b2e14b3af5df699876dd4ff3acd00b7f",
        "files": [
            {
                "filename": "README.md",
                "status": "added",
                "additions": 9,
                "deletions": 0,
                "changes": 9
                # Missing patch field
            },
            {
                "filename": "styles.css",
                "status": "added",
                "additions": 17,
                "deletions": 0,
                "changes": 17
                # Missing patch field
            }
        ]
    }