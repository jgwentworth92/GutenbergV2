from enum import Enum


# available status
class StepStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Service(Enum):
    GATEWAY_SERVICE = "gateway_service"
    GITHUB_SERVICE = "github_service"
    COMMIT_SUMMARY = "commit_summary_service"
    QDRANT_SERVICE = "qdrant_service"


STEP_TYPE_MAPPING = {
    Service.GATEWAY_SERVICE: "gateway",
    Service.GITHUB_SERVICE: "data_processing",
    Service.COMMIT_SUMMARY: "data_processing_llm",
    Service.QDRANT_SERVICE: "data_sink",
}
