import pytest
import orjson

from unittest.mock import patch, Mock

from config.config_setting import config
from dataflows.gateway_service import process_message

from bytewax.connectors.kafka import (
    KafkaSinkMessage,
    KafkaSourceMessage,
)
from bytewax import operators as op


@pytest.fixture
def mock_requests():
    get_request_mock = Mock()
    get_request_mock.json.return_value = [
        {
            "step_type": "gateway",
            "id": "760b4637-43c8-421c-968d-58321ca0d4c5",
        }
    ]
    get_request_mock.status_code = 200
    get_request_mock.raise_for_status = Mock()

    post_request_mock = Mock()
    post_request_mock.status_code = 200
    post_request_mock.raise_for_status = Mock()

    with patch(
        "requests.Session.get", return_value=get_request_mock
    ) as get_patch, patch(
        "requests.Session.patch", return_value=post_request_mock
    ) as patch_patch:
        yield get_patch, patch_patch


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
def test_gateway_service(
    deb_message, expected_topic, create_dataflow, run_dataflow, mock_requests
):
    get_patch, patch_patch = mock_requests
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
    get_patch.assert_called_once_with(
        "http://fastapi:8000/steps/job/760b4637-43c8-421c-968d-58321ca0d4c5"
    )
    patch_patch.assert_called_once_with(
        "http://fastapi:8000/steps/760b4637-43c8-421c-968d-58321ca0d4c5",
        json={"status": "COMPLETE"},
    )
