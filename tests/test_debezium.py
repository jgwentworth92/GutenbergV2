import uuid
import time
import json

from sqlalchemy import text


def test_insert_user_into_database_and_check_kafka(postgres_engine, consume_messages):
    _id = uuid.uuid4()
    data = json.dumps({"data": "github"})
    with postgres_engine.connect() as connection:
        insert_query = text(
            f"INSERT INTO resources (id, job_id, resource_type, resource_data, created_at, updated_at)"
            f"VALUES ('{_id}', '{_id}', 'github', '{json.dumps(data)}', '2024-06-18T00:55:47.311424Z', '2024-06-18T00:55:47.311424Z');"
        )
        connection.execute(insert_query)
        connection.commit()
        time.sleep(20)

    processed_messages = consume_messages("resource_topic", num_messages=2)
    assert any(
        [
            message["payload"].get("after", {}).get("id", None) == str(_id)
            for message in processed_messages
        ]
    )
