from uuid import UUID
import requests
from config.config_setting import config
from models.constants import Service, StepStatus, STEP_TYPE_MAPPING
from logging_config import get_logger

logger = get_logger(__name__)


class UserManagementClient:
    def __init__(self):
        self.base_url = config.USER_MANAGEMENT_SERVICE_URL
        self.session = requests.Session()

    def update_status(self, job_id: UUID, step_type: str, status: StepStatus, extra_data: dict = None):
        """
        Update the status of a job step. Optionally update total documents or increment document count.

        :param job_id: UUID of the job
        :param step_type: Type of the step
        :param status: Status of the step
        :param extra_data: Optional dictionary containing extra data like total_documents or increment_count
        """
        logger.info(f"Updating step for job: {job_id}, step type: {step_type} with status: {status}")

        data = {"job_id": job_id, "step_type": step_type, "status": status}

        if extra_data:
            data.update(extra_data)

        response = self.session.put(
            f"{self.base_url}/jobs/{job_id}/steps/{step_type}",
            json=data
        )
        response.raise_for_status()
        logger.info(f"Step updated successfully for job: {job_id}, step type: {step_type}")
        return response.json()

    def get_job_status(self, job_id: UUID):
        logger.info(f"Getting status for job: {job_id}")
        response = self.session.get(f"{self.base_url}/jobs/{job_id}/status")
        response.raise_for_status()
        return response.json()

    def close(self):
        self.session.close()


user_management_service = UserManagementClient()
