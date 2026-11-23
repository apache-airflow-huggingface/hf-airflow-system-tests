#!/usr/bin/env python3
"""Write the secret-bearing Breeze environment and container init scripts."""

import json
import os
import shlex
from pathlib import Path


def main() -> None:
    variables_target = Path(os.environ["BREEZE_VARIABLES_FILE"])
    init_target = Path(os.environ["BREEZE_INIT_FILE"])

    run_id = os.environ["GITHUB_RUN_ID"]
    org = os.environ["HF_TEST_HUB_ORG"].strip()
    token = os.environ["HF_TOKEN_AIRFLOW"].strip().strip('"').strip("'")
    conn_json = json.dumps({
        "conn_type": "huggingface",
        "password": token,
    })
    env_vars = {
        "SYSTEM_TESTS_ENV_ID": run_id,
        "HF_TEST_HUB_ORG": org,
        "AIRFLOW_CONN_HUGGINGFACE_DEFAULT": conn_json,
        "AIRFLOW__CORE__DAGS_FOLDER": "/opt/airflow/providers/huggingface/tests/system/huggingface",
        "AIRFLOW__CORE__LOAD_EXAMPLES": "False",
    }

    variables_target.parent.mkdir(parents=True, exist_ok=True)
    variables_target.write_text(
        "\n".join(f"export {key}={shlex.quote(value)}" for key, value in env_vars.items()) + "\n",
        encoding="utf-8",
    )
    variables_target.chmod(0o600)

    init_script = '''#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${AIRFLOW_CONN_HUGGINGFACE_DEFAULT:-}" ]]; then
  echo "ERROR: AIRFLOW_CONN_HUGGINGFACE_DEFAULT was not exported inside the Breeze container!" >&2
  exit 1
fi
echo "Breeze init.sh: AIRFLOW_CONN_HUGGINGFACE_DEFAULT verified."

'''
    init_target.write_text(init_script, encoding="utf-8")
    init_target.chmod(0o700)


if __name__ == "__main__":
    main()
