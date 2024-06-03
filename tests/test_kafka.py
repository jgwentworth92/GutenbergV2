import json

import pytest
from config.config_setting import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC
qdrant_output=config.VECTORDB_TOPIC_NAME


def test_kafka_integration(produce_messages, consume_messages):
    input_topic = "your_input_topic"
    output_topic = "your_output_topic"
    processed_topic = "your_processed_topic"
    qdrant_output = "your_qdrant_output_topic"

    # Produce test messages to the input topic
    test_messages = [
        {"owner": "octocat", "repo_name": "Hello-World"},
        {"owner": "octocat", "repo_name": "Spoon-Knife"}
    ]
    logger.info("Starting Kafka integration test...")
    produce_messages(input_topic, test_messages)
    logger.info("Test messages produced to input topic.")

    # Consume messages from the output topic and verify
    try:
        processed_messages = consume_messages(output_topic, num_messages=2)
        logger.info(f"Consumed {len(processed_messages)} messages from output topic.")
        assert len(processed_messages) > 0, "No messages consumed from output topic"

        for msg in processed_messages:
            msg = json.loads(msg)
            logger.info(f"Processed message: {msg}")
            assert "page_content" in msg
            assert "metadata" in msg
            metadata = msg['metadata']
            assert "id" in metadata
            assert "author" in metadata
            assert "date" in metadata
            assert "repo_name" in metadata
            assert "commit_url" in metadata
            assert "filename" in metadata
            assert "status" in metadata
            assert "additions" in metadata
            assert "deletions" in metadata
            assert "changes" in metadata
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the processed topic and verify
    try:
        processed_messages = consume_messages(processed_topic, num_messages=2)
        logger.info(f"Consumed {len(processed_messages)} messages from processed topic.")
        assert len(processed_messages) > 0, "No messages consumed from processed topic"

        for msg in processed_messages:
            msg = json.loads(msg)
            logger.info(f"Final processed message: {msg}")
            assert "page_content" in msg
            assert "metadata" in msg
            metadata = msg['metadata']
            assert "id" in metadata
            assert "author" in metadata
            assert "date" in metadata
            assert "repo_name" in metadata
            assert "commit_url" in metadata
            assert "filename" in metadata
            assert "status" in metadata
            assert "additions" in metadata
            assert "deletions" in metadata
            assert "changes" in metadata
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the Qdrant output topic and verify
    try:
        final_messages = consume_messages(qdrant_output, num_messages=2)
        logger.info(f"Consumed {len(final_messages)} messages from qdrant output topic.")
        assert len(final_messages) > 0, "No messages consumed from qdrant output topic"

        for msg in final_messages:
            msg = json.loads(msg)
            logger.info(f"Final processed message: {msg}")
            assert "id" in msg
            assert "collection_name" in msg
            assert msg["collection_name"] == "Hello-World"
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    logger.info("Kafka integration test completed successfully.")