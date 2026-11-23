"""Run a secret-safe Hugging Face connection check as an Airflow task."""

from __future__ import annotations

import os

import pendulum

from airflow.providers.huggingface.hooks.huggingface import HuggingFaceHook
from airflow.sdk import DAG, task
from tests_common.test_utils.system_tests import get_test_run


CONN_ID = "huggingface_default"

with DAG(
    dag_id="huggingface_connection_diagnostic",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
) as dag:

    @task
    def check_huggingface_connection() -> None:
        connection_env_present = bool(os.environ.get("AIRFLOW_CONN_HUGGINGFACE_DEFAULT"))
        hook = HuggingFaceHook(CONN_ID)
        try:
            connection = hook.get_connection(CONN_ID)
        except Exception as exc:
            raise AssertionError(
                "huggingface_default lookup failed through Airflow's task connection API; "
                f"AIRFLOW_CONN_HUGGINGFACE_DEFAULT present in task process="
                f"{connection_env_present}, "
                f"error={type(exc).__name__}"
            ) from None

        if not connection.password:
            raise AssertionError(
                "huggingface_default resolved in the task process, but its password is empty; "
                f"AIRFLOW_CONN_HUGGINGFACE_DEFAULT present={connection_env_present}"
            )

        try:
            hook.get_conn().whoami()
        except Exception as exc:
            raise AssertionError(
                "huggingface_default resolved through Airflow's task connection API, "
                "but Hugging Face rejected whoami(); check that HF_TOKEN_AIRFLOW is valid "
                "and authorized, "
                f"AIRFLOW_CONN_HUGGINGFACE_DEFAULT present in task process="
                f"{connection_env_present}, error={type(exc).__name__}"
            ) from None

    check_huggingface_connection()

test_run = get_test_run(dag)
