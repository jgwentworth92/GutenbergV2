from services.vectordb_service import process_message_to_vectordb


def test_qdrant(create_dataflow, run_dataflow, fake_event_data):
    flow, captured_output = create_dataflow(lambda msg: process_message_to_vectordb(msg), fake_event_data)
    run_dataflow(flow)

    for msg in captured_output:
        assert "id" in msg
        assert "collection_name" in msg
        assert "job_id" in msg
        assert msg["collection_name"] == "Hello-World"
        assert msg["vector_db_id"] == ["8996e7f9-4ea3-1fd2-3d59-55d74de62da4"]
    assert len(captured_output) > 0
