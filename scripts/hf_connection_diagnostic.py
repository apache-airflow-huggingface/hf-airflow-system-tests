"""Check that the Hugging Face Airflow connection is available to system tests."""

import pytest

from airflow.providers.huggingface.hooks.huggingface import HuggingFaceHook


def test_huggingface_default_connection_authenticates() -> None:
    hook = HuggingFaceHook("huggingface_default")

    try:
        connection = hook.get_connection("huggingface_default")
    except Exception as exc:
        pytest.fail(f"huggingface_default lookup failed: {type(exc).__name__}")

    if not connection.password:
        pytest.fail("huggingface_default resolved, but its password is empty")

    try:
        hook.get_conn().whoami()
    except Exception as exc:
        pytest.fail(
            "huggingface_default has a password, but Hugging Face authentication "
            f"failed: {type(exc).__name__}"
        )
