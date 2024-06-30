from logging import Logger
from langchain_core.callbacks import BaseCallbackHandler

class MyCustomHandler(BaseCallbackHandler):
    def __init__(self, logger: Logger):
        """
        Initialize the custom handler with a specific logger.

        Args:
            logger (Logger): A Logger object used for logging events and messages within this handler. It logs various actions and events occurring throughout the lifecycle of language model operations, including token generation, process starts and ends, and errors.
        """
        self.logger = logger

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.logger.info(f"New token: {token}")

    def on_llm_start(self, serialized, prompts, run_id, **kwargs):
        self.logger.info(f"LLM start with run_id: {run_id} and prompts: {prompts}")

    def on_llm_end(self, response, run_id, parent_run_id=None, **kwargs):
        self.logger.info(f"LLM end with run_id: {run_id} and response: {response}")

    def on_llm_error(self, error, run_id, parent_run_id=None, **kwargs):
        self.logger.error(f"LLM error with run_id: {run_id} and error: {error}")

    def on_chain_start(self, serialized, inputs, run_id, **kwargs):
        self.logger.info(f"Chain start with run_id: {run_id} and inputs: {inputs}")

    def on_chain_end(self, outputs, run_id, parent_run_id=None, **kwargs):
        self.logger.info(f"Chain end with run_id: {run_id} and outputs: {outputs}")

    def on_chain_error(self, error, run_id, parent_run_id=None, **kwargs):
        self.logger.error(f"Chain error with run_id: {run_id} and error: {error}")

    def on_retriever_start(self, serialized, query, run_id, **kwargs):
        self.logger.info(f"Retriever start with run_id: {run_id} and query: {query}")

    def on_retriever_end(self, documents, run_id, parent_run_id=None, **kwargs):
        self.logger.info(f"Retriever end with run_id: {run_id} and documents: {documents}")

    def on_retriever_error(self, error, run_id, parent_run_id=None, **kwargs):
        self.logger.error(f"Retriever error with run_id: {run_id} and error: {error}")
