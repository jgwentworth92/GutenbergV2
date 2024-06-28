from unittest.mock import MagicMock
import httpx
import pytest
from bytewax.outputs import StatelessSinkPartition
from dataflow_connectors.fastapi_connector import FastAPIConnector, FastAPISink



def test_fastapi_connector_initialization(sample_url, sample_auth_header, sample_prepare_payload):
    connector = FastAPIConnector(sample_url, sample_auth_header, sample_prepare_payload)
    assert isinstance(connector, StatelessSinkPartition)
    assert connector.url == sample_url
    assert connector.auth_header == sample_auth_header

def test_fastapi_connector_write_batch_success(mock_httpx_client, sample_url, sample_auth_header, sample_prepare_payload):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.return_value.post.return_value = mock_response

    connector = FastAPIConnector(sample_url, sample_auth_header, sample_prepare_payload)
    connector.write_batch(["test_item"])

    mock_httpx_client.return_value.post.assert_called_once_with(
        sample_url,
        headers=sample_auth_header,
        json=[{"key": "value"}]
    )

def test_fastapi_connector_write_batch_error(mock_httpx_client, sample_url, sample_auth_header, sample_prepare_payload, caplog):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
    mock_httpx_client.return_value.post.return_value = mock_response

    connector = FastAPIConnector(sample_url, sample_auth_header, sample_prepare_payload)
    connector.write_batch(["test_item"])

    assert "An error occurred" in caplog.text

def test_fastapi_sink_initialization(sample_url, sample_auth_header, sample_prepare_payload):
    sink = FastAPISink(sample_url, sample_auth_header, sample_prepare_payload)
    assert sink.url == sample_url
    assert sink.auth_header == sample_auth_header

def test_fastapi_sink_build(sample_url, sample_auth_header, sample_prepare_payload):
    sink = FastAPISink(sample_url, sample_auth_header, sample_prepare_payload)
    connector = sink.build("step_1", 0, 1)
    assert isinstance(connector, FastAPIConnector)
    assert connector.url == sample_url
    assert connector.auth_header == sample_auth_header

@pytest.mark.parametrize("input_data,expected_calls", [
    (["item1", "item2"], 2),
    ([], 0),
    (["single_item"], 1)
])
def test_fastapi_connector_write_batch_multiple_items(mock_httpx_client, sample_url, sample_auth_header, sample_prepare_payload, input_data, expected_calls):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_httpx_client.return_value.post.return_value = mock_response

    connector = FastAPIConnector(sample_url, sample_auth_header, sample_prepare_payload)
    connector.write_batch(input_data)

    assert mock_httpx_client.return_value.post.call_count == expected_calls
