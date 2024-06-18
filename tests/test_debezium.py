import uuid
import logging
import time
import json

import pytest

from sqlalchemy import text

logger = logging.getLogger(__name__)


def test_insert_user_into_database_and_check_kafka(postgres_engine, consume_messages):
    username = uuid.uuid4()
    data = json.dumps({"data": "github"})
    with postgres_engine.connect() as connection:
        insert_query = text(
            f"INSERT INTO resource_table (resource_type, resource_data) VALUES ('{username}', {data});"
        )
        connection.execute(insert_query)
        connection.commit()
        time.sleep(20)

    processed_messages = consume_messages("resource_topic", num_messages=2)
    assert any(
        [
            message["payload"].get("after", {}).get("resource_type", None) == str(username)
            for message in processed_messages
        ]
    )
