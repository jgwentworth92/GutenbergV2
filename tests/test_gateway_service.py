import pytest
import orjson

from config.config_setting import config
from dataflows.gateway_service import process_message

from bytewax.connectors.kafka import (
    KafkaSinkMessage,
    KafkaSourceMessage,
)
from bytewax import operators as op


@pytest.mark.parametrize(
    "deb_message, expected_topic",
    [
        (
            {
                "id": "d1b66acf-269b-4fb2-893e-ad78a5205112",
                "job_id": "760b4637-43c8-421c-968d-58321ca0d4c5",
                "resource_type": "github",
                "resource_data": '{"test": "test"}',
                "created_at": "2024-06-18T00:55:47.311424Z",
                "updated_at": "2024-06-18T00:55:47.311424Z",
            },
            config.GITHUB_TOPIC,
        ),
        (
            {
                "id": "d1b66acf-269b-4fb2-893e-ad78a5205112",
                "job_id": "760b4637-43c8-421c-968d-58321ca0d4c5",
                "resource_type": "pdf",
                "resource_data": '{"test": "test"}',
                "created_at": "2024-06-18T00:55:47.311424Z",
                "updated_at": "2024-06-18T00:55:47.311424Z",
            },
            config.PDF_INPUT,
        ),
    ],
)
def test_gateway_service(deb_message, expected_topic, create_dataflow, run_dataflow):
    captured_output: list[KafkaSinkMessage]
    flow, captured_output = create_dataflow(
        process_message,
        KafkaSourceMessage(
            key=None, value=orjson.dumps({"payload": {"after": deb_message}})
        ),
        op.map,
    )
    run_dataflow(flow)
    assert len(captured_output) == 1
    assert captured_output[0].topic == expected_topic
