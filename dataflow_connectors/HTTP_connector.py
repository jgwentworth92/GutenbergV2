from bytewax.outputs import StatelessSinkPartition, DynamicSink
from typing import List, Callable, Any, Dict
import httpx
import json

from logging_config import get_logger

logger = get_logger(__name__)


class RetryTransport(httpx.BaseTransport):
    def __init__(self, transport: httpx.BaseTransport, retries: int = 3):
        self._transport = transport
        self._retries = retries

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        retries_left = self._retries
        while retries_left > 0:
            try:
                response = self._transport.handle_request(request)
                if response.status_code in {502, 503, 504}:
                    raise httpx.HTTPStatusError("Server error", request=request, response=response)
                return response
            except (httpx.TransportError, httpx.HTTPStatusError):
                retries_left -= 1
                if retries_left == 0:
                    raise


class HTTPConnector(StatelessSinkPartition):
    def __init__(self, url: str, auth_header: Dict[str, str], prepare_payload: Callable[[Any], List[Dict]],
                 timeout: int = 10, max_retries: int = 3):
        """
        Initializes the connector with URL, authentication details, and a function to prepare payloads.

        :param url: The endpoint URL to which the data will be posted.
        :param auth_header: Authentication headers required for the API.
        :param prepare_payload: A function that takes an item and returns a list of JSON-serializable dictionaries.
        :param timeout: The request timeout in seconds.
        :param max_retries: The maximum number of retries for a failed request.
        """
        self.url = url
        self.auth_header = auth_header
        transport = RetryTransport(transport=httpx.HTTPTransport(), retries=max_retries)
        self.client = httpx.Client(transport=transport, timeout=timeout)
        self.prepare_payload = prepare_payload

    def write_batch(self, items: List[Any]) -> None:
        for item in items:
            logger.info(f"passed in data is {item}")
            payloads = self.prepare_payload(item)
            try:
                response = self.client.post(self.url, headers=self.auth_header, json=payloads)
                response.raise_for_status()
                logger.info(f"Response status code: {response.status_code}")
            except Exception as e:
                logger.error(f"An error occurred: {e} with data {payloads}")

    def close(self) -> None:
        """
        Close the HTTP client.
        """
        self.client.close()

    def __del__(self):
        """Ensure clean-up."""
        self.client.close()


class HTTPSink(DynamicSink):
    def __init__(self, url: str, auth_header: Dict[str, str], prepare_payload: Callable[[Any], List[Dict]]):
        """
        Initializes the dynamic sink with the URL, authentication details, and a function to prepare payloads.

        :param url: The endpoint URL to which the data will be posted.
        :param auth_header: Authentication headers required for the API.
        :param prepare_payload: A function that takes an item and returns a JSON-serializable dictionary.
        """
        self.url = url
        self.auth_header = auth_header
        self.prepare_payload = prepare_payload

    def build(self, _step_id, _worker_index, _worker_count):
        """
        Build and return a partition for writing data.

        :param _step_id: The step ID.
        :param _worker_index: The index of the worker.
        :param _worker_count: The total number of workers.
        :return: An instance of HTTPConnector.
        """
        return HTTPConnector(self.url, self.auth_header, self.prepare_payload)
