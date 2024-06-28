import pytest
import json
import time

from services.pdf_processing_service import process_pdf




def test_process_pdf_success(sample_pdf_input):
    # Process the PDF
    results = list(process_pdf(sample_pdf_input))

    # Assertions
    assert len(results) > 0
    for result in results:
        parsed_result = json.loads(result)
        assert 'page_content' in parsed_result
        assert parsed_result['metadata']['collection_name'] == "pdftest"
        assert parsed_result['metadata']['job_id'] == "02ccd381-76e7-47ee-9346-b69df29cc640"
        assert parsed_result['metadata']['vector_id'].startswith("https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf")

def test_process_pdf_invalid_input():
    invalid_input = {"resource_data": "invalid json"}
    results = list(process_pdf(invalid_input))
    assert len(results) == 0  # No results should be produced for invalid input

def test_process_pdf_nonexistent_url(sample_pdf_input):
    sample_pdf_input['resource_data'] = json.dumps({
        "pdf_url": "https://example.com/nonexistent.pdf",
        "collection_name": "pdftest"
    })
    results = list(process_pdf(sample_pdf_input))
    assert len(results) == 0  # No results should be produced for nonexistent URL

def test_process_pdf_timing(sample_pdf_input):
    start_time = time.time()
    results = list(process_pdf(sample_pdf_input))
    end_time = time.time()

    assert len(results) > 0
    assert end_time - start_time < 30  # Assuming processing should take less than 30 seconds

@pytest.mark.parametrize("pdf_url", [
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf",
])
def test_process_different_pdfs(sample_pdf_input, pdf_url):
    sample_pdf_input['resource_data'] = json.dumps({
        "pdf_url": pdf_url,
        "collection_name": "pdftest"
    })
    results = list(process_pdf(sample_pdf_input))
    assert len(results) > 0
    for result in results:
        parsed_result = json.loads(result)
        assert 'page_content' in parsed_result
        assert parsed_result['metadata']['collection_name'] == "pdftest"
        assert parsed_result['metadata']['vector_id'].startswith(pdf_url)