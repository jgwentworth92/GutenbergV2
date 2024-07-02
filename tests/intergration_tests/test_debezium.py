import uuid
import time
import json
import pytest

from sqlalchemy import text


@pytest.mark.skip(reason="Flaky test, temporarily disabled")
def test_insert_user_into_database_and_check_kafka(postgres_engine, consume_messages):
    _id = uuid.uuid4()
    data = json.dumps({"data": "github"})
    with postgres_engine.connect() as connection:
        insert_job_query = text(
            "INSERT INTO jobs (id, user_id, created_at, updated_at) "
            "VALUES ('3ba11cee-80e8-4212-acb5-660a25a603b1', '3ba11cee-80e8-4212-acb5-660a25a603b0', '2024-06-18T00:55:47.311424Z', '2024-06-18T00:55:47.311424Z') "
            "RETURNING id;"
        )
        result = connection.execute(insert_job_query)
        job_id = result.fetchone()[0]
        insert_query = text(
            f"INSERT INTO resources (id, job_id, resource_type, resource_data, created_at, updated_at)"
            f"VALUES ('{_id}', '{job_id}', 'github', '{json.dumps(data)}', '2024-06-18T00:55:47.311424Z', '2024-06-18T00:55:47.311424Z');"
        )
        connection.execute(insert_query)
        connection.commit()
        time.sleep(20)

    processed_messages = consume_messages("resource_topic", num_messages=20)
    assert any(
        [
            message["payload"].get("after", {}).get("id", None) == str(_id)
            for message in processed_messages
        ]
    )
