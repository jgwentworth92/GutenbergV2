import pytest
from bytewax.connectors.kafka import KafkaSinkMessage
from services.gateway_routing import kafka_to_standardized, process_and_route_message_base
from utils.status_update import StandardizedMessage

def test_kafka_to_standardized(mock_kafka_source_message):
    result = kafka_to_standardized(mock_kafka_source_message)
    assert isinstance(result, StandardizedMessage)
    assert result.job_id == "123"
    assert result.step_number == 1
    assert result.data == {'job_id': '123', 'resource_type': 'github'}
    assert result.metadata == {"original_topic": "test_topic"}

@pytest.mark.parametrize("resource_type, expected_topic", [
    ("github", "github_topic"),
    ("pdf", "pdfInput"),
    ("unknown", None)
])
def test_process_and_route_message_base(resource_type, expected_topic):
    # Arrange
    message = StandardizedMessage(
        job_id="test_job",
        step_number=1,
        data={"resource_type": resource_type},
        metadata={}
    )

    # Act
    result = process_and_route_message_base(message)

    # Assert
    if expected_topic:
        assert isinstance(result, KafkaSinkMessage)
        assert result.topic == expected_topic
        assert result.key is None
        assert isinstance(result.value, str)  # Assuming model_dump_json() returns a string
    else:
        assert result is None




def test_process_and_route_message_base_logging(caplog):
    message = StandardizedMessage(
        job_id="test_job",
        step_number=1,
        data={"resource_type": "unknown"},
        metadata={}
    )

    process_and_route_message_base(message)

    assert "Unrecognised resource type unknown for job test_job" in caplog.text