import bytewax.operators as op
from bytewax.dataflow import Dataflow
from bytewax.testing import TestingSource, run_main, TestingSink
from github import Github
from icecream import ic
from dataclasses import dataclass
from typing import List, Optional

from kafkaGithubConsumer.githubConsumer import fetch_and_emit_commits

# Define CommitData and FileInfo dataclasses
@dataclass
class FileInfo:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str]

@dataclass
class CommitData:
    author: str
    message: str
    date: str
    url: str
    repo_name: str
    commit_id: str
    files: List[FileInfo]

    def dict(self):
        return self.__dict__

sample_repo_info_1 = {"owner": "octocat", "repo_name": "Hello-World"}
sample_repo_info_2 = {"owner": "octocat", "repo_name": "Spoon-Knife"}
invalid_repo_info = {"owner": "invalid", "repo_name": "invalid-repo"}


def run_test(repo_info, repo_name):
    # Create the dataflow
    flow = Dataflow(f"Github_Repo_Test_{repo_name}")

    # Define the input source
    inp = op.input(
        "inp",
        flow,
        TestingSource(
            [repo_info]
        ),
    )

    # Inspect the input
    _ = op.inspect("check_inp", inp)

    # Map the input to fetch and emit commits
    commits = op.flat_map("fetch_and_emit_commits", inp, fetch_and_emit_commits)

    # Inspect the emitted commits
    _ = op.inspect("check_commits", commits)

    # Capture output using TestingSink
    captured_output = []
    op.output("capture_output", commits, TestingSink(captured_output))

    # Run the dataflow
    run_main(flow)

    # Assertions
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

    print(f"All assertions passed for repo: {repo_name}")
    print(f"Captured output for repo {repo_name}: {captured_output}")


def test_github_commits_hello_world():
    run_test(sample_repo_info_1, "Hello-World")

def test_github_commits_spoon_knife():
    run_test(sample_repo_info_2, "Spoon-Knife")

def test_github_commits_invalid_repo():
    run_test(invalid_repo_info, "invalid-repo")


if __name__ == "__main__":
    test_github_commits_hello_world()
    test_github_commits_spoon_knife()
    test_github_commits_invalid_repo()
