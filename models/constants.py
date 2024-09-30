from enum import Enum


# available status
class StepStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Service(Enum):
    GATEWAY_SERVICE = "gateway"
    DATAFLOW_TYPE_processing_llm = "data_processing_llm"
    DATAFLOW_TYPE_processing_raw="data_processing"
    DATAFLOW_TYPE_DATASINK = "data_sink"

STEP_TYPE_MAPPING = {Service.GATEWAY_SERVICE: "gateway",Service.DATAFLOW_TYPE_processing_llm:"data_processing_llm",Service.DATAFLOW_TYPE_processing_raw:"data_processing_llm",Service.DATAFLOW_TYPE_DATASINK :"data_sink"}
