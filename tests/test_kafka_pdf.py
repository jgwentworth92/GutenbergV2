import pytest
import logging
import json
from config.config_setting import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pdfinput = config.PDF_INPUT
input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC
qdrant_output = config.VECTORDB_TOPIC_NAME


def produce_and_verify_messages(produce_messages, consume_messages, topic, test_messages, verify_function,
                                num_messages=2):
    produce_messages(topic, test_messages)
    try:
        consumed_messages = consume_messages(topic, num_messages=num_messages)
        verify_function(consumed_messages)
    except TimeoutError as e:
        assert False, str(e)


def verify_pdf_message_structure(messages):
    assert len(messages) > 0, "No messages consumed from topic"
    for msg in messages:
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


def verify_final_message_structure(messages):
    assert len(messages) > 0, "No messages consumed from topic"
    final_ids = []
    for msg in messages:
        if isinstance(msg, str):
            msg = json.loads(msg)
        elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
            msg = json.loads(msg[0])
        assert isinstance(msg, dict), f"Message is not a dictionary: {msg}"
        assert "id" in msg, f"Missing 'id' in {msg}"
        assert "collection_name" in msg, f"Missing 'collection_name' in {msg}"
        assert msg["collection_name"] == "pdftest"
        final_ids.append(msg["id"])
    return final_ids


def test_kafka_pdf_processing_integration(produce_messages, consume_messages, setup_pdf_dataflows, manage_kafka_topics):
    test_messages = [{
        "pdf_url": "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf",
        "collection_name": "pdftest"
    }]

    produce_and_verify_messages(produce_messages, consume_messages, pdfinput, test_messages,
                                verify_pdf_message_structure)

    # Verify messages in output topic
    produce_and_verify_messages(produce_messages, consume_messages, output_topic, test_messages,
                                verify_pdf_message_structure)

    # Verify messages in processed topic
    produce_and_verify_messages(produce_messages, consume_messages, processed_topic, test_messages,
                                verify_pdf_message_structure)

    # Verify final messages in qdrant output topic
    produce_messages(pdfinput, test_messages)
    try:
        final_messages = consume_messages(qdrant_output, num_messages=2)
        final_ids = verify_final_message_structure(final_messages)
        expected_ids = [
            "12a0d0d9-79ac-f57f-495d-f563b68d6ffa",
            "039e559d-845d-0d8d-b837-02df2c92498b",
            "8996e7f9-4ea3-1fd2-3d59-55d74de62da4"
        ]
        assert any(id in final_ids for id in
                   expected_ids), f"None of the expected IDs are present. Expected: {expected_ids}, but got: {final_ids}"
    except TimeoutError as e:
        assert False, str(e)
