import pytest
from unittest.mock import patch
from utils.status_update import StandardizedMessage, status_updater, update_status
from models.constants import Service, StepStatus


def test_update_status():
    with patch('utils.status_update.user_management_service.update_status') as mock_update_status:
        job_id = "test_job_id"
        service = Service.DATAFLOW_TYPE_processing_raw
        status = StepStatus.IN_PROGRESS

        update_status(job_id, service, status)

        mock_update_status.assert_called_once_with(
            job_id, service.value, status.value
        )


def test_status_updater_success():
    @status_updater(Service.DATAFLOW_TYPE_processing_raw)
    def test_function(message: StandardizedMessage):
        return StandardizedMessage(job_id=message.job_id, step_number=2, data={"result": "success"})

    with patch('utils.status_update.update_status') as mock_update_status:
        input_message = StandardizedMessage(job_id="test_job", step_number=1, data={})
        result = test_function(input_message)

        assert isinstance(result, StandardizedMessage)
        assert result.data == {"result": "success"}

        mock_update_status.assert_any_call("test_job", Service.DATAFLOW_TYPE_processing_raw, StepStatus.IN_PROGRESS)
        mock_update_status.assert_any_call("test_job", Service.DATAFLOW_TYPE_processing_raw, StepStatus.COMPLETE)


def test_status_updater_failure():
    @status_updater(Service.DATAFLOW_TYPE_processing_raw)
    def test_function(message: StandardizedMessage):
        raise Exception("Test error")

    with patch('utils.status_update.update_status') as mock_update_status:
        input_message = StandardizedMessage(job_id="test_job", step_number=1, data={})
        result = test_function(input_message)

        assert result is None

        mock_update_status.assert_any_call("test_job", Service.DATAFLOW_TYPE_processing_raw, StepStatus.IN_PROGRESS)
        mock_update_status.assert_any_call("test_job", Service.DATAFLOW_TYPE_processing_raw, StepStatus.FAILED)


def test_status_updater_generator():
    @status_updater(Service.DATAFLOW_TYPE_processing_raw)
    def test_generator(message: StandardizedMessage):
        yield StandardizedMessage(job_id=message.job_id, step_number=2, data={"result": "part1"})
        yield StandardizedMessage(job_id=message.job_id, step_number=3, data={"result": "part2"})

    with patch('utils.status_update.update_status') as mock_update_status:
        input_message = StandardizedMessage(job_id="test_job", step_number=1, data={})
        result = test_generator(input_message)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].data == {"result": "part1"}
        assert result[1].data == {"result": "part2"}

        mock_update_status.assert_any_call("test_job", Service.DATAFLOW_TYPE_processing_raw, StepStatus.IN_PROGRESS)
        mock_update_status.assert_any_call("test_job", Service.DATAFLOW_TYPE_processing_raw, StepStatus.COMPLETE)