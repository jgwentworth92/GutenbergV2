import pytest
from config.config_setting import config
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pdfinput = config.PDF_INPUT
input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC
qdrant_output = config.VECTORDB_TOPIC_NAME

def test_kafka_pdf_processing_integration(produce_messages, consume_messages, setup_bytewax_dataflows):
    # Produce test messages to the input topic
    test_messages = [{
        "pdf_url": "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf",
        "collection_name": "pdftest"
    }]
    logger.info("Starting Kafka PDF processing integration test...")
    produce_messages(pdfinput, test_messages)
    logger.info("Test messages produced to input topic.")

    def verify_message_structure(messages):
        assert len(messages) > 0, "No messages consumed from topic"
        for msg in messages:
            logger.info(f"Message content: {msg}")
            # Ensure the message is a dictionary, convert from JSON if necessary
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list):
                msg = [json.loads(m) if isinstance(m, str) else m for m in msg]
            assert isinstance(msg, dict) or (isinstance(msg, list) and all(isinstance(m, dict) for m in msg)), f"Message is not a dictionary or list of dictionaries: {msg}"

            if isinstance(msg, dict):
                msgs = [msg]
            else:
                msgs = msg

            for m in msgs:
                assert "page_content" in m, f"Missing 'page_content' in {m}"
                assert "metadata" in m, f"Missing 'metadata' in {m}"
                metadata = m['metadata']
                required_fields = [
                    "vector_id", "collection_name", "page"
                ]
                for field in required_fields:
                    assert field in metadata, f"Missing '{field}' in metadata: {metadata}"

    # Expected IDs (replace with actual expected IDs)
    expected_ids = [
        "991f256c687a081288504cd62c63799f",
        "c42f5594801a70a6731cd6a0f7ea5b08",
        "73b4871b295b16659674778e9e8e9022",
        "2a42a4998502167b5a54f568f0358497",
        "25e467c6d0f340784d5b8fb9727c2c30",
        "961e85abdf35bf7f8eb25383af4fbbc2"
    ]

    # Consume messages from the output topic and verify
    try:
        processed_messages = consume_messages(output_topic, num_messages=6)
        logger.info(f"Consumed {len(processed_messages)} messages from output topic.")
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the processed topic and verify
    try:
        processed_messages = consume_messages(processed_topic, num_messages=6)
        logger.info(f"Consumed {len(processed_messages)} messages from processed topic.")
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    # Consume messages from the Qdrant output topic and verify
    try:
        final_messages = consume_messages(qdrant_output, num_messages=6)
        logger.info(f"Consumed {len(final_messages)} messages from qdrant output topic.")
        assert len(final_messages) > 0, "No messages consumed from qdrant output topic"

        final_ids = []
        for msg in final_messages:
            logger.info(f"Final processed message: {msg}")
            # Ensure the message is a dictionary, convert from JSON if necessary
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list):
                msg = [json.loads(m) if isinstance(m, str) else m for m in msg]
            assert isinstance(msg, dict) or (isinstance(msg, list) and all(isinstance(m, dict) for m in msg)), f"Message is not a dictionary or list of dictionaries: {msg}"

            if isinstance(msg, dict):
                msgs = [msg]
            else:
                msgs = msg

            for m in msgs:
                assert "id" in m, f"Missing 'id' in {m}"
                assert "collection_name" in m, f"Missing 'collection_name' in {m}"
                assert m["collection_name"] == "pdftest"
                final_ids.append(m["id"])

        # Verify that the same IDs are produced each time
        assert any(id in final_ids for id in expected_ids), f"None of the expected IDs are present. Expected: {expected_ids}, but got: {final_ids}"
    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    logger.info("Kafka PDF processing integration test completed successfully.")
