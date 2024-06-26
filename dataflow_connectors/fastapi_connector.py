from bytewax.outputs import StatelessSinkPartition, DynamicSink
from typing import List, Callable, Any, Dict
import httpx
import json

from logging_config import get_logger

logger = get_logger(__name__)


class FastAPIConnector(StatelessSinkPartition):
    def __init__(self, url: str, auth_header: Dict[str, str], prepare_payload: Callable[[Any], List[Dict]]):
        """
        Initializes the connector with URL, authentication details, and a function to prepare payloads.

        :param url: The endpoint URL to which the data will be posted.
        :param auth_header: Authentication headers required for the API.
        :param prepare_payload: A function that takes an item and returns a list of JSON-serializable dictionaries.
        """
        self.url = url
        self.auth_header = auth_header
        self.client = httpx.Client()
        self.prepare_payload = prepare_payload

    def write_batch(self, items: List[Any]) -> None:
        for item in items:
            logger.info(f"passed in data is {item}")
            payloads = self.prepare_payload(item)
            for payload in payloads:
                try:
                    response = self.client.post(self.url, headers=self.auth_header, json=payload)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"An error occurred: {e} with data {payload}")

    def close(self) -> None:
        """
        Close the HTTP client.
        """
        self.client.close()

    def __del__(self):
        """Ensure clean-up."""
        self.client.close()



class FastAPISink(DynamicSink):
    def __init__(self, url: str, auth_header: Dict[str, str], prepare_payload: Callable[[Any], Dict]):
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
        :return: An instance of FastAPIConnector.
        """
        return FastAPIConnector(self.url, self.auth_header, self.prepare_payload)
