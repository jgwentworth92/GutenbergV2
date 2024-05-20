import pytest
from config.config_setting import config

input_topic = config.INPUT_TOPIC
output_topic = config.OUTPUT_TOPIC
processed_topic = config.PROCESSED_TOPIC


def test__kafka_integration(produce_messages, consume_messages):
    # Produce test messages to the input topic
    test_messages = [
        {"owner": "octocat", "repo_name": "Hello-World"},
        {"owner": "octocat", "repo_name": "Spoon-Knife"}
    ]
    produce_messages(input_topic, test_messages)

    # Consume messages from the output topic and verify
    processed_messages = consume_messages(output_topic, num_messages=2)
    for msg in processed_messages:
        assert "commit_id" in msg
        assert "author" in msg
        assert "message" in msg
        assert "date" in msg
        assert "url" in msg
        assert "repo_name" in msg
        assert "files" in msg

    # Consume messages from the processed topic and verify
    final_messages = consume_messages(processed_topic, num_messages=2)
    for msg in final_messages:
        assert "page_content" in msg
        assert "metadata" in msg


