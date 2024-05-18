from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink, KafkaSinkMessage
import orjson  # For serialization
from pydantic import BaseModel
from typing import List, Optional
from github import Github
from kafka.errors import KafkaError
from icecream import ic
from confluent_kafka import OFFSET_END

from kafkaGithubConsumer.config_setting import get_config

# Application setup
config = get_config()

# Kafka broker addresses
brokers = [config.BROKERS]
# Input and output Kafka topics
input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC

# Separate Kafka configurations for consumer and producer
consumer_config = config.CONSUMER_CONFIG
producer_config = config.PRODUCER_CONFIG

# Bytewax dataflow setup
flow = Dataflow("github_commit_processing")


# Define dataclasses for structured commit data
class FileInfo(BaseModel):
    """Class representing file information in a commit."""
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None


class CommitData(BaseModel):
    """Class representing commit data."""
    author: str
    message: str
    date: str
    url: str
    repo_name: str
    commit_id: str
    files: List[FileInfo]


def fetch_and_emit_commits(repo_info):
    """
    Fetch commits from a GitHub repository and emit them one at a time.

    Parameters:
    repo_info (dict): Dictionary containing the owner and repository name.

    Yields:
    dict: Commit data or error information.
    """
    owner = repo_info["owner"]
    repo_name = repo_info["repo_name"]
    token = config.GITHUB_TOKEN
    g = Github(token)

    ic(f"Fetching repository {owner}/{repo_name}")
    try:
        # Get the repository object from GitHub
        repo = g.get_repo(f"{owner}/{repo_name}")
    except Exception as e:
        # Log and yield an error message if repository fetching fails
        error_message = {
            "error": "Failed to fetch repository",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        }
        ic(error_message)
        yield error_message
        return  # Stop further processing if repo fetching fails

    try:
        # Fetch commits from the repository
        for commit in repo.get_commits():
            try:
                # Extract commit details and yield the commit data
                commit_data = CommitData(
                    author=commit.commit.author.name,
                    message=commit.commit.message,
                    date=commit.commit.author.date.isoformat(),
                    url=commit.html_url,
                    repo_name=repo.name,
                    commit_id=commit.sha,
                    files=[FileInfo(
                        filename=file.filename,
                        status=file.status,
                        additions=file.additions,
                        deletions=file.deletions,
                        changes=file.changes,
                        patch=getattr(file, 'patch', None)
                    ) for file in commit.files]
                )
                ic(f"Processed commit ID {commit_data.commit_id} for repo {commit_data.repo_name}")
                yield commit_data.dict()
            except Exception as e:
                # Log and yield an error message if commit processing fails
                error_message = {
                    "error": "Failed to process commit",
                    "details": str(e),
                    "commit_id": commit.sha
                }
                ic(error_message)
                yield error_message
    except Exception as e:
        # Log and yield an error message if fetching commits fails
        error_message = {
            "error": "Failed to fetch commits",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        }
        ic(error_message)
        yield error_message


def inspect_output_topic(index, message):
    """
    Inspect messages from the output Kafka topic.

    Parameters:
    index (int): The index of the message.
    message (KafkaError or bytes): The message from the Kafka topic.
    """
    if isinstance(message, KafkaError):
        ic(f"Error: {message}")
    else:
        ic(orjson.loads(message.value))


# Input from Kafka topic
kafka_input = op.input("kafka-in", flow,
                       KafkaSource(brokers=brokers, starting_offset=OFFSET_END, topics=[input_topic],
                                   add_config=consumer_config))

# Fetch and emit each commit individually
processed_commits = op.flat_map("fetch_and_emit_commits", kafka_input,
                                lambda msg: fetch_and_emit_commits(orjson.loads(msg.value)))

# Serialize each commit data
serialized_commits = op.map("serialize_commits", processed_commits, orjson.dumps)

# Create KafkaSinkMessages for each serialized commit data
kafka_messages = op.map("create_kafka_messages", serialized_commits, lambda x: KafkaSinkMessage(None, x))

# Output serialized data to Kafka
op.output("kafka-output", kafka_messages, KafkaSink(brokers=brokers, topic=output_topic, add_config=producer_config))

# Input from Kafka, deserialize each message
kafka_output_input = op.input("kafka-output-input", flow,
                              KafkaSource(brokers=brokers, starting_offset=OFFSET_END, topics=[output_topic],
                                          add_config=consumer_config))

# Inspect the output topic messages
op.inspect("inspect_output_topic", kafka_output_input, inspect_output_topic)
