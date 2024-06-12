import time

import pytest
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.testing import TestingSource, TestingSink, run_main
import logging
from typing import Dict, Any
from confluent_kafka import Producer, Consumer, KafkaException
from config.config_setting import get_config
import subprocess
import orjson

config = get_config()
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Kafka configuration for the test
kafka_brokers = config.BROKERS


@pytest.fixture(scope="module")
def setup_bytewax_dataflows():
    logger.info("Starting Bytewax dataflows...")
    # Start the Bytewax dataflows
    github_commit_processing = subprocess.Popen(
        ["python", "-m", "bytewax.run", "-w3", "dataflows.github_commit_processing"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    commit_summary_service = subprocess.Popen(
        ["python", "-m", "bytewax.run", "-w3", "dataflows.commit_summary_service"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    qdrant_service = subprocess.Popen(
        ["python", "-m", "bytewax.run", "-w3", "dataflows.add_qdrant_service"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    # Give some time for the services to start
    time.sleep(10)
    logger.info("Bytewax dataflows started.")

    yield

    logger.info("Terminating Bytewax dataflows...")
    # Terminate the Bytewax dataflows
    github_commit_processing.terminate()
    commit_summary_service.terminate()
    qdrant_service.terminate()
    github_commit_processing.wait()
    commit_summary_service.wait()
    qdrant_service.wait()
    logger.info("Bytewax dataflows terminated.")

@pytest.fixture(scope="module")
def setup_pdf_dataflows():
    logger.info("Starting Bytewax dataflows...")
    # Start the Bytewax dataflows
    input_processing = subprocess.Popen(
        ["python", "-m", "bytewax.run", "-w3", "dataflows.pdfProcessing"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    commit_summary_service = subprocess.Popen(
        ["python", "-m", "bytewax.run", "-w3", "dataflows.commit_summary_service"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    qdrant_service = subprocess.Popen(
        ["python", "-m", "bytewax.run", "-w3", "dataflows.add_qdrant_service"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    # Give some time for the services to start
    time.sleep(10)
    logger.info("Bytewax dataflows started.")

    yield

    logger.info("Terminating Bytewax dataflows...")
    # Terminate the Bytewax dataflows
    input_processing.terminate()
    commit_summary_service.terminate()
    qdrant_service.terminate()
    input_processing.wait()
    commit_summary_service.wait()
    qdrant_service.wait()
    logger.info("Bytewax dataflows terminated.")
@pytest.fixture
def produce_messages():
    def _produce_messages(topic, messages):
        producer_config = {
            "bootstrap.servers": kafka_brokers,
        }
        producer = Producer(producer_config)

        logger.info(f"Producing {len(messages)} messages to topic '{topic}'...")
        for message in messages:
            producer.produce(topic, orjson.dumps(message).decode('utf-8'))

        producer.flush()
        logger.info("Messages produced.")

    return _produce_messages


@pytest.fixture
def consume_messages():
    def _consume_messages(topic, num_messages, timeout=60):
        consumer_config = {
            "bootstrap.servers": kafka_brokers,
            "group.id": "test-group",
            "auto.offset.reset": "latest"
        }
        consumer = Consumer(consumer_config)
        consumer.subscribe([topic])

        messages = []
        start_time = time.time()
        logger.info(f"Consuming messages from topic '{topic}'...")
        while len(messages) < num_messages and (time.time() - start_time) < timeout:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            messages.append(orjson.loads(msg.value().decode('utf-8')))

        consumer.close()
        logger.info(f"Consumed {len(messages)} messages.")
        return messages

    return _consume_messages


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
    return ["{\"page_content\":\"Filename: README, Status: added, Files: @@ -0,0 +1 @@\\n+Hello World!\\n\\\\ No newline at end of file\",\"metadata\":{\"filename\":\"README\",\"status\":\"added\",\"additions\":1,\"deletions\":0,\"changes\":1,\"author\":\"cameronmcefee\",\"date\":\"2011-01-26T19:06:08+00:00\",\"repo_name\":\"Hello-World\",\"commit_url\":\"https://github.com/octocat/Hello-World/commit/553c2077f0edc3d5dc5d17262f6aa498e69d6f8e\",\"id\":\"553c2077f0edc3d5dc5d17262f6aa498e69d6f8e\",\"token_count\":18,\"collection_name\":\"Hello-World\",\"vector_id\":\"553c2077f0edc3d5dc5d17262f6aa498e69d6f8eREADME\"},\"type\":\"Document\"}"]


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


@pytest.fixture
def qdrant_event_data():
    return {
        "page_content": "Filename: README, Status: modified, Files: @@ -1 +1 @@\n-Hello World!\n\\ No newline at end of file\n+Hello World!",
        "metadata": {
            "filename": "README",
            "status": "modified",
            "additions": 1,
            "deletions": 1,
            "changes": 2,
            "author": "The Octocat",
            "date": "2012-03-06T23:06:50+00:00",
            "repo_name": "Hello-World",
            "commit_url": "https://github.com/octocat/Hello-World/commit/7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
            "id": "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
            "token_count": 20,
            "collection_name": f"The Octocat_Hello-World"
        }
    }
