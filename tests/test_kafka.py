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

def test_kafka_github_processing_integration(produce_messages, consume_messages, setup_bytewax_dataflows, manage_kafka_topics):
    test_messages = [{"owner": "octocat", "repo_name": "Hello-World"}]
    produce_messages(input_topic, test_messages)

    def verify_message_structure(messages):
        assert len(messages) > 0
        for msg in messages:
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
                msg = json.loads(msg[0])
            assert isinstance(msg, dict)
            assert "page_content" in msg
            assert "metadata" in msg
            metadata = msg['metadata']
            required_fields = [
                "id", "author", "date", "repo_name", "commit_url",
                "filename", "status", "additions", "deletions", "changes"
            ]
            for field in required_fields:
                assert field in metadata

    expected_ids = [
        "12a0d0d9-79ac-f57f-495d-f563b68d6ffa",
        "039e559d-845d-0d8d-b837-02df2c92498b",
        "8996e7f9-4ea3-1fd2-3d59-55d74de62da4"
    ]

    try:
        processed_messages = consume_messages(output_topic, num_messages=2)
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        assert False, str(e)

    try:
        processed_messages = consume_messages(processed_topic, num_messages=2)
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        assert False, str(e)

    try:
        final_messages = consume_messages(qdrant_output, num_messages=2)
        assert len(final_messages) > 0

        final_ids = []
        for msg in final_messages:
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
                msg = json.loads(msg[0])
            assert isinstance(msg, dict)
            assert "id" in msg
            assert "collection_name" in msg
            assert msg["collection_name"] == "Hello-World"
            final_ids.append(msg["id"][0])

        assert any(id in final_ids for id in expected_ids)
    except TimeoutError as e:
        assert False, str(e)

def test_kafka_pdf_processing_integration(produce_messages, consume_messages, setup_pdf_dataflows, manage_kafka_topics):
    test_messages = [{
        "pdf_url": "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf",
        "collection_name": "pdftest"
    }]
    produce_messages(pdfinput, test_messages)

    def verify_message_structure(messages):
        assert len(messages) > 0
        for msg in messages:
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
                msg = json.loads(msg[0])
            assert isinstance(msg, dict)
            assert "page_content" in msg
            assert "metadata" in msg
            metadata = msg['metadata']
            required_fields = [
                "vector_id", "collection_name", "page"
            ]
            for field in required_fields:
                assert field in metadata
    try:
        processed_messages = consume_messages(output_topic, num_messages=2)
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        assert False, str(e)

    try:
        processed_messages = consume_messages(processed_topic, num_messages=2)
        verify_message_structure(processed_messages)
    except TimeoutError as e:
        assert False, str(e)

    try:
        final_messages = consume_messages(qdrant_output, num_messages=2)
        assert len(final_messages) > 0

        final_ids = []
        for msg in final_messages:
            if isinstance(msg, str):
                msg = json.loads(msg)
            elif isinstance(msg, list) and len(msg) == 1 and isinstance(msg[0], str):
                msg = json.loads(msg[0])
            assert isinstance(msg, dict)
            assert "id" in msg
            assert "collection_name" in msg
            assert msg["collection_name"] == "pdftest"
            final_ids.append(msg["id"])

    except TimeoutError as e:
        assert False, str(e)
