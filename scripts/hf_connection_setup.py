"""Make the Hugging Face test connection available through Airflow's API."""

from __future__ import annotations

import json
import os

from airflow.models import Connection
from airflow.utils.session import create_session


def pytest_sessionstart(session) -> None:
    """Persist the test connection before system-test DAGs execute."""
    serialized_connection = os.environ.get("AIRFLOW_CONN_HUGGINGFACE_DEFAULT")
    if not serialized_connection:
        raise RuntimeError("AIRFLOW_CONN_HUGGINGFACE_DEFAULT is not configured")

    connection_data = json.loads(serialized_connection)
    connection = Connection(
        conn_id="huggingface_default",
        conn_type=connection_data["conn_type"],
        host=connection_data.get("host"),
        login=connection_data.get("login"),
        password=connection_data.get("password"),
        schema=connection_data.get("schema"),
        extra=json.dumps(connection_data["extra"])
        if isinstance(connection_data.get("extra"), dict)
        else connection_data.get("extra"),
    )

    with create_session() as db_session:
        db_session.merge(connection)
