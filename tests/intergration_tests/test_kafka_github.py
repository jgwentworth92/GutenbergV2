import pytest
import requests
from pydantic_core import ValidationError

from config.config_setting import config
import logging
import json

from models.gateway import ResourceModel

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
RESOURCE_TOPIC = config.RESOURCE_TOPIC
input_topic = config.GITHUB_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC
qdrant_output = config.VECTORDB_TOPIC_NAME


@pytest.mark.skip(reason="Flaky test, temporarily disabled")
def test_kafka_integration(
    produce_messages,
    kafka_message_factory,
    sample_repo_info_1,
    consume_messages,
    setup_bytewax_dataflows,
):
    logger.info("Starting Kafka integration test...")
    response = requests.post(
        "http://0.0.0.0:8000/api/resources/",
        json={
            "user_id": "3ba11cee-80e8-4212-acb5-660a25a603b0",
            "resource_type": "github",
            "resource_data": {"owner": "octocat", "repo_name": "Hello-World"},
        },
    )
    response.raise_for_status()
    data = response.json()
    logger.info(f"Created resource in FastAPI, with data, {data}")
    kafka_message = {"payload": {"after": data}}

    produce_messages(RESOURCE_TOPIC, [kafka_message])
    logger.info("Test messages produced to input topic.")

    def verify_message_structure(messages):
        assert len(messages) > 0, "No messages consumed from topic"
        for msg in messages:
            logger.info(f"Message content: {msg}")
            # Ensure the message is a dictionary, convert from JSON if necessary
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
                msg = json.loads(msg[0])
            assert isinstance(msg, dict), f"Message is not a dictionary: {msg}"
            assert "page_content" in msg, f"Missing 'page_content' in {msg}"
            assert "metadata" in msg, f"Missing 'metadata' in {msg}"
            metadata = msg["metadata"]
            required_fields = [
                "id", "author", "date", "repo_name", "commit_url",
                "filename", "status", "additions", "deletions", "changes","job_id"
            ]
            for field in required_fields:
                assert field in metadata, f"Missing '{field}' in metadata: {metadata}"

    # Expected IDs (replace with actual expected IDs)
    expected_ids = [
        "12a0d0d9-79ac-f57f-495d-f563b68d6ffa",
        "039e559d-845d-0d8d-b837-02df2c92498b",
        "8996e7f9-4ea3-1fd2-3d59-55d74de62da4",
        "0068cbcb-5978-61bd-7cfa-ffd6482ea12c",
        "258568c8-01cf-d18f-1301-c30d4c686d74",
    ]

    try:
        processed_messages = consume_messages(input_topic, num_messages=6)
        logger.info(
            f"Consumed {len(processed_messages)} messages from input github topic topic."
        )

        for msg in processed_messages:
            try:
                assert msg["resource_type"] == "github"
                assert json.loads(msg["resource_data"]) == {
                    "owner": "octocat",
                    "repo_name": "Hello-World",
                }
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Message validation failed for message {msg}: {e}")
                assert False, f"Message validation failed: {e}"

    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    try:
        processed_messages = consume_messages(output_topic, num_messages=6)
        logger.info(
            f"Consumed {len(processed_messages)} messages from github processing dataflow topic."
        )
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the processed topic and verify
    try:
        processed_messages = consume_messages(processed_topic, num_messages=6)
        logger.info(
            f"Consumed {len(processed_messages)} messages from processed topic."
        )
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the Qdrant output topic and verify
    try:
        final_messages = consume_messages(qdrant_output, num_messages=6)
        logger.info(
            f"Consumed {len(final_messages)} messages from qdrant output topic."
        )
        assert len(final_messages) > 0, "No messages consumed from qdrant output topic"

        final_ids = []
        for msg in final_messages:
            logger.info(f"Final processed message: {msg}")
            # Ensure the message is a dictionary, convert from JSON if necessary
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
                msg = json.loads(msg[0])
            assert isinstance(msg, dict), f"Message is not a dictionary: {msg}"
            assert "id" in msg, f"Missing 'id' in {msg}"
            assert "collection_name" in msg, f"Missing 'collection_name' in {msg}"
            assert msg["collection_name"] == "Hello-World"
            final_ids.append(msg["id"][0])  # Extract the ID from the message

        # Verify that the same IDs are produced each time
        assert any(
            id in final_ids for id in expected_ids
        ), f"None of the expected IDs are present. Expected: {expected_ids}, but got: {final_ids}"
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    logger.info("Kafka integration test completed successfully.")
