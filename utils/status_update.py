from typing import Any, Callable, Generator
from dataclasses import dataclass
from datetime import datetime
from models import constants
from services.user_management_service import user_management_service
from logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class StandardizedMessage:
    job_id: str
    step_number: int
    data: Any
    metadata: dict
    timestamp: str = datetime.utcnow().isoformat()


def update_status(job_id: str, service: constants.Service, status: constants.StepStatus):
    logger.info(f"Updating status for job {job_id}: service={service.value}, status={status.value}")
    user_management_service.update_status(job_id, service.value, status.value)
    logger.info(f"Status updated successfully for job {job_id}")


def create_status_updater(service: constants.Service):
    def create_processor_with_status(
            process_func: Callable[[StandardizedMessage], Generator[StandardizedMessage, None, None]]):
        def process_with_status(message: StandardizedMessage) -> Generator[StandardizedMessage, None, None]:
            job_id = message.job_id

            logger.info(f"Setting status to IN_PROGRESS for job {job_id}")
            update_status(job_id, service, constants.StepStatus.IN_PROGRESS)

            try:
                logger.info(f"Processing data for job {job_id}")
                results = list(process_func(message))

                if results:
                    logger.info(f"Processing successful for job {job_id} with{results}")
                    update_status(job_id, service, constants.StepStatus.COMPLETE)
                    yield from results
                else:
                    logger.warning(f"Processing yielded no results for job {job_id} with {results}")
                    update_status(job_id, service, constants.StepStatus.FAILED)

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {str(e)}")
                update_status(job_id, service, constants.StepStatus.FAILED)

        return process_with_status

    return create_processor_with_status
