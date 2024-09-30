from functools import wraps
from typing import Callable, Generator, Union, List, Any, Dict, Iterable, Optional

from pydantic import BaseModel, Field

from models import constants
from models.document import Document
from services.user_management_service import user_management_service
from logging_config import get_logger

logger = get_logger(__name__)


class StandardizedMessage(BaseModel):
    """
    A standardized message format for consistent data handling across services.

    Attributes:
        job_id (str): Unique identifier for the job.
        step_number (int): The current step number in the processing pipeline.
        data (Union[Dict[str, Any], List[Any], str]): The main payload of the message.
            Can be a dictionary, a list, or a string.
        metadata (Dict[str, Any]): Additional information about the message and its processing.
    """
    job_id: str
    step_number: int
    data: Union[Dict[str, Any], List[Any], str, List[Document]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt: Optional[str] = None
    llm_model: Optional[str] = None

def update_status(job_id: str, service: constants.Service, status: constants.StepStatus):
    """
    Update the status of a job for a specific service.

    Args:
        job_id (str): The unique identifier of the job.
        service (constants.Service): The service updating the status.
        status (constants.StepStatus): The new status of the job.
    """
    logger.info(f"Updating status for job {job_id}: service={service.value}, status={status.value}")
    try:
        user_management_service.update_status(job_id, service.value, status.value)
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")


def status_updater(service: constants.Service):
    """
    A decorator that wraps a function to provide automatic status updates for a job.

    This decorator handles both regular functions and generator functions. It updates
    the job status to IN_PROGRESS before execution, and then to COMPLETE or FAILED
    after execution, depending on the result.

    Args:
        service (constants.Service): The service that is processing the job.

    Returns:
        Callable: A decorator function.

    Usage:
        @status_updater(constants.Service.MY_SERVICE)
        def my_processing_function(message: StandardizedMessage) -> Union[StandardizedMessage, None]:
            # Process the message
            return processed_message
    """

    def decorator(func: Callable[[StandardizedMessage], Union[StandardizedMessage, None, Generator, Iterable]]):
        @wraps(func)
        def wrapper(message: StandardizedMessage) -> Iterable[Union[StandardizedMessage, None]]:
            job_id = message.job_id

            try:

                update_status(job_id, service, constants.StepStatus.IN_PROGRESS)

                result = func(message)

                if isinstance(result, Generator) or (
                        isinstance(result, Iterable) and not isinstance(result, (str, bytes, StandardizedMessage))):
                    results = list(result)
                elif result is None:
                    results = []
                else:
                    results = [result]

                if not any(results):
                    logger.warning(f"Processing yielded no results for job {job_id}")
                    status = constants.StepStatus.FAILED
                    results = [None]  # Ensure we always return an iterable
                else:
                    logger.info(f"Processing successful for job {job_id}")
                    status = constants.StepStatus.COMPLETE

                update_status(job_id, service, status)
                return results

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {str(e)}")
                update_status(job_id, service, constants.StepStatus.FAILED)
                return [None]  # Return an iterable with None to indicate failure

        return wrapper

    return decorator
