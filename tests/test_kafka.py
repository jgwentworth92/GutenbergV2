import pytest
from config.config_setting import config
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
pdfinput=config.PDF_INPUT
input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC
qdrant_output = config.VECTORDB_TOPIC_NAME

def test_kafka_github_processing_integration(produce_messages, consume_messages,setup_bytewax_dataflows):
    # Produce test messages to the input topic
    test_messages = [
        {"owner": "octocat", "repo_name": "Hello-World"}
    ]
    logger.info("Starting Kafka integration test...")
    produce_messages(input_topic, test_messages)
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
            metadata = msg['metadata']
            required_fields = [
                "id", "author", "date", "repo_name", "commit_url",
                "filename", "status", "additions", "deletions", "changes"
            ]
            for field in required_fields:
                assert field in metadata, f"Missing '{field}' in metadata: {metadata}"

    # Expected IDs (replace with actual expected IDs)
    expected_ids = [
        "12a0d0d9-79ac-f57f-495d-f563b68d6ffa",
        "039e559d-845d-0d8d-b837-02df2c92498b",
        "8996e7f9-4ea3-1fd2-3d59-55d74de62da4"
    ]



    # Consume messages from the output topic and verify
    try:
        processed_messages = consume_messages(output_topic, num_messages=2)
        logger.info(f"Consumed {len(processed_messages)} messages from output topic.")
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the processed topic and verify
    try:
        processed_messages = consume_messages(processed_topic, num_messages=2)
        logger.info(f"Consumed {len(processed_messages)} messages from processed topic.")
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the Qdrant output topic and verify
    try:
        final_messages = consume_messages(qdrant_output, num_messages=2)
        logger.info(f"Consumed {len(final_messages)} messages from qdrant output topic.")
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
        assert any(id in final_ids for id in
                   expected_ids), f"None of the expected IDs are present. Expected: {expected_ids}, but got: {final_ids}"
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    logger.info("Kafka integration test completed successfully.")



def test_kafka_pdf_processing_integration(produce_messages, consume_messages, setup_pdf_dataflows):
    # Produce test messages to the input topic
    test_messages = [
        {
            "pdf_url": "https://arxiv.org/pdf/2103.15348",
            "collection_name": "pdftest"
        }
    ]
    logger.info("Starting Kafka PDF integration test...")
    produce_messages("pdfinput", test_messages)
    logger.info("Test messages produced to pdf input topic.")

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
            metadata = msg['metadata']
            required_fields = [
                "vector_id", "collection_name", "page"
            ]
            for field in required_fields:
                assert field in metadata, f"Missing '{field}' in metadata: {metadata}"

    # Expected IDs (replace with actual expected IDs)
    expected_ids = [
        "12a0d0d9-79ac-f57f-495d-f563b68d6ffa",
        "039e559d-845d-0d8d-b837-02df2c92498b",
        "8996e7f9-4ea3-1fd2-3d59-55d74de62da4"
    ]

    # Consume messages from the output topic and verify
    try:
        processed_messages = consume_messages("output_topic", num_messages=2)
        logger.info(f"Consumed {len(processed_messages)} messages from output topic.")
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the processed topic and verify
    try:
        processed_messages = consume_messages("processed_topic", num_messages=2)
        logger.info(f"Consumed {len(processed_messages)} messages from processed topic.")
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the Qdrant output topic and verify
    try:
        final_messages = consume_messages("qdrant_output", num_messages=2)
        logger.info(f"Consumed {len(final_messages)} messages from qdrant output topic.")
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
            assert msg["collection_name"] == "pdftest"
            final_ids.append(msg["id"])  # Extract the ID from the message

        # Verify that the same IDs are produced each time
        assert any(id in final_ids for id in expected_ids), f"None of the expected IDs are present. Expected: {expected_ids}, but got: {final_ids}"
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    logger.info("Kafka integration test completed successfully.")

