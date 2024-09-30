import pytest
from config.config_setting import config
import logging
import json
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pdfinput = config.PDF_INPUT
input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC
qdrant_output = config.VECTORDB_TOPIC_NAME
resource_topic=config.RESOURCE_TOPIC

@pytest.mark.skip(reason="Flaky test, temporarily disabled")
def test_kafka_pdf_processing_integration(produce_messages, kafka_message_factory, consume_messages,
                                          setup_bytewax_dataflows):
    # Produce test messages to the input topic
    test_messages = {
        "id": "3dc6752c-b27a-4243-8fe2-810bf482313b",
        "job_id": "02ccd381-76e7-47ee-9346-b69df29cc640",
        "resource_type": "pdf",
        "resource_data": "{\"pdf_url\": \"https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf\", \"collection_name\": \"pdftest\"}",
        "created_at": "2024-06-19T23:33:49.763648Z",
        "updated_at": "2024-06-19T23:33:49.763648Z"}
    kafka_message = kafka_message_factory(test_messages)
    logger.info("Starting Kafka PDF processing integration test...")
    produce_messages(pdfinput,[test_messages])
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
            assert isinstance(msg, dict) or (isinstance(msg, list) and all(
                isinstance(m, dict) for m in msg)), f"Message is not a dictionary or list of dictionaries: {msg}"

            if isinstance(msg, dict):
                msgs = [msg]
            else:
                msgs = msg

            for m in msgs:
                assert "page_content" in m, f"Missing 'page_content' in {m}"
                assert "metadata" in m, f"Missing 'metadata' in {m}"
                metadata = m['metadata']
                required_fields = [
                    "vector_id", "collection_name", "page","job_id"
                ]
                for field in required_fields:
                    assert field in metadata, f"Missing '{field}' in metadata: {metadata}"

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
        time.sleep(10)

        final_messages = consume_messages(qdrant_output, num_messages=6)
        logger.info(f"Consumed {len(final_messages)} messages from qdrant output topic.")
        for msg in final_messages:
            logger.info(f"Final processed message: {msg}")
            # Ensure the message is a dictionary, convert from JSON if necessary
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list):
                msg = [json.loads(m) if isinstance(m, str) else m for m in msg]
            assert isinstance(msg, dict) or (isinstance(msg, list) and all(
                isinstance(m, dict) for m in msg)), f"Message is not a dictionary or list of dictionaries: {msg}"

            if isinstance(msg, dict):
                msgs = [msg]
            else:
                msgs = msg

            for m in msgs:
                assert "id" in m, f"Missing 'id' in {m}"
                assert "collection_name" in m, f"Missing 'collection_name' in {m}"
                assert m["collection_name"] == "pdftest"

    except TimeoutError as e:
        logger.error(e)
        assert False, str(e)

    logger.info("Kafka PDF processing integration test completed successfully.")
