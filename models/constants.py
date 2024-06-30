from enum import Enum


# available status
class StepStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Service(Enum):
    GATEWAY_SERVICE = "gateway_service"


STEP_TYPE_MAPPING = {Service.GATEWAY_SERVICE: "gateway"}
