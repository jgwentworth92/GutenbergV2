import requests

from config.config_setting import config
from models.constants import Service, StepStatus, STEP_TYPE_MAPPING
from logging_config import get_logger


logger = get_logger(__name__)


class UserManagementClient:
    def __init__(self):
        self.base_url = config.USER_MANAGEMENT_SERVICE_URL
        self.session = requests.Session()

    def fetch_step_id(self, job_id: str, service: Service):
        response = self.session.get(f"{self.base_url}/steps/job/{job_id}")
        response.raise_for_status()
        data = response.json()
        filtered_data = [
            item for item in data if item["step_type"] == STEP_TYPE_MAPPING[service]
        ]
        assert (
            len(filtered_data) <= 1
        ), f"Found multiple steps for {service} {filtered_data}"
        assert len(filtered_data) > 0, f"No step found for {service}"
        return filtered_data[0]["id"]

    def update_status(self, service: Service, job_id: str, status: StepStatus):
        logger.info(f"Retrieving Step Id for job: {job_id}")
        logger.info(f"Updating the status of the step to {status}")
        step_id = self.fetch_step_id(job_id, service)
        response = self.session.patch(
            f"{self.base_url}/steps/{step_id}", json={"status": status}
        )
        response.raise_for_status()

    def close(self):
        self.session.close()


user_management_service = UserManagementClient()
