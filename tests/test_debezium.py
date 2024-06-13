import uuid
import logging

import pytest

from sqlalchemy import text

logger = logging.getLogger(__name__)


def test_insert_user_into_database_and_check_kafka(postgres_engine, consume_messages):
    username = uuid.uuid4()
    with postgres_engine.connect() as connection:
        insert_query = text(f"INSERT INTO app_user (username) VALUES ('{username}');")
        connection.execute(insert_query)
        connection.commit()

    processed_messages = consume_messages("custom_topic", num_messages=2)
    assert any(
        [
            message["payload"].get("after", {}).get("username", None) == str(username)
            for message in processed_messages
        ]
    )
