import pytest
import orjson
from services.pdf_processing_service import process_pdf
from utils.status_update import StandardizedMessage




def test_process_pdf_success(sample_pdf_input):
    # Process the PDF and convert the generator into a list
    results = list(process_pdf(sample_pdf_input))

    # Assert that results are not None and are iterable
    assert results is not None, "Expected non-None response from process_pdf"
    assert len(results) > 0, "Expected at least one result from PDF processing"

    for result in results:
        # Ensure that the result is a valid StandardizedMessage
        assert isinstance(result, StandardizedMessage), f"Expected StandardizedMessage, got {type(result)}"

        # Check the job_id and step_number
        assert result.job_id == sample_pdf_input.job_id, f"Expected job_id {sample_pdf_input.job_id}, got {result.job_id}"
        assert result.step_number == sample_pdf_input.step_number, f"Expected step_number {sample_pdf_input.step_number}, got {result.step_number}"

        # Ensure that data is a list
        assert isinstance(result.data, list), f"Expected 'data' to be a list, got {type(result.data)}"

        for doc in result.data:
            # Parse the serialized document
            parsed_doc = orjson.loads(doc)

            # Check for 'page_content' and 'metadata' in the parsed document
            assert "page_content" in parsed_doc, f"Missing 'page_content' in {parsed_doc}"
            assert "metadata" in parsed_doc, f"Missing 'metadata' in {parsed_doc}"

            # Extract metadata and ensure the expected fields are present
            metadata = parsed_doc["metadata"]
            expected_metadata_keys = [
                "collection_name", "job_id", "doc_type", "vector_id", "page"
            ]
            for key in expected_metadata_keys:
                assert key in metadata, f"Missing '{key}' in metadata: {metadata}"

            # Verify specific metadata values
            assert metadata[
                       "collection_name"] == "test", f"Expected collection_name 'test', got {metadata['collection_name']}"
            assert metadata[
                       "job_id"] == sample_pdf_input.job_id, f"Expected job_id {sample_pdf_input.job_id}, got {metadata['job_id']}"
            assert metadata["vector_id"].startswith("https://arxiv.org/pdf/2409.13794"), \
                f"Expected vector_id to start with the PDF URL, got {metadata['vector_id']}"


@pytest.mark.parametrize("input_data, expected_length, description", [
    # Invalid JSON in resource_data
    ({
         "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
         "step_number": 1,
         "data": {
             "id": "65f77dc5-1283-49d6-9424-22bc547dd473",
             "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
             "resource_type": "pdf",
             "resource_data": "Invalid JSON",  # Intentionally malformed
             "created_at": "2024-09-30T17:17:28.231396Z",
             "updated_at": "2024-09-30T17:17:28.231396Z"
         },
         "metadata": {
             "original_topic": "resource_topic"
         },
         "prompt": None,
         "llm_model": None
     }, 0, "Expected no results for invalid JSON input"),

    # Missing resource_data field
    ({
         "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
         "step_number": 1,
         "data": {
             "id": "65f77dc5-1283-49d6-9424-22bc547dd473",
             "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
             "resource_type": "pdf",
             # Missing resource_data
             "created_at": "2024-09-30T17:17:28.231396Z",
             "updated_at": "2024-09-30T17:17:28.231396Z"
         },
         "metadata": {
             "original_topic": "resource_topic"
         },
         "prompt": None,
         "llm_model": None
     }, 0, "Expected no results for missing resource_data"),

    # Invalid URL in pdf_url
    ({
         "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
         "step_number": 1,
         "data": {
             "id": "65f77dc5-1283-49d6-9424-22bc547dd473",
             "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
             "resource_type": "pdf",
             "resource_data": "{\"pdf_url\": \"https://invalid-url\", \"collection_name\": \"test\", \"prompt\": \"test\", \"llm_model\": \"openai\"}",
             "created_at": "2024-09-30T17:17:28.231396Z",
             "updated_at": "2024-09-30T17:17:28.231396Z"
         },
         "metadata": {
             "original_topic": "resource_topic"
         },
         "prompt": None,
         "llm_model": None
     }, 0, "Expected no results for invalid URL in pdf_url"),

    # Empty pdf_url
    ({
         "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
         "step_number": 1,
         "data": {
             "id": "65f77dc5-1283-49d6-9424-22bc547dd473",
             "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
             "resource_type": "pdf",
             "resource_data": "{\"pdf_url\": \"\", \"collection_name\": \"test\", \"prompt\": \"test\", \"llm_model\": \"openai\"}",
             "created_at": "2024-09-30T17:17:28.231396Z",
             "updated_at": "2024-09-30T17:17:28.231396Z"
         },
         "metadata": {
             "original_topic": "resource_topic"
         },
         "prompt": None,
         "llm_model": None
     }, 0, "Expected no results for empty pdf_url"),

    # Empty dictionary for missing data field (instead of None)
    ({
         "job_id": "83a47a96-8144-42ed-815a-6409fad83a40",
         "step_number": 1,
         "data": {},  # Empty dictionary instead of None
         "metadata": {
             "original_topic": "resource_topic"
         },
         "prompt": None,
         "llm_model": None
     }, 0, "Expected no results for missing data field")
])
def test_process_pdf_edge_cases(input_data, expected_length, description):
    # Create the StandardizedMessage using the input_data
    message = StandardizedMessage(
        job_id=input_data["job_id"],
        step_number=input_data["step_number"],
        data=input_data["data"],
        metadata=input_data["metadata"],
        prompt=input_data["prompt"],
        llm_model=input_data["llm_model"]
    )

    # Process the PDF and convert the generator into a list
    results = list(process_pdf(message))

    # Assert the length of the results matches the expected length
    assert len(results) == expected_length, description