#!/usr/bin/env python3
"""Write the secret-bearing Breeze environment and container init scripts."""

import json
import os
import shlex
from pathlib import Path


def main() -> None:
    variables_target = Path(os.environ["BREEZE_VARIABLES_FILE"])
    init_target = Path(os.environ["BREEZE_INIT_FILE"])

    run_id = f"{os.environ['GITHUB_RUN_ID']}-{os.environ['GITHUB_RUN_ATTEMPT']}"
    org = os.environ["HF_TEST_HUB_ORG"].strip()
    token = os.environ["HF_TOKEN_AIRFLOW"].strip().strip('"').strip("'")
    conn_json = json.dumps({
        "conn_type": "huggingface",
        "password": token,
        "extra": {"token": token},
    })
    env_vars = {
        "HF_AIRFLOW_SYSTEM_TEST_RUN_ID": run_id,
        "HF_TEST_HUB_ORG": org,
        "HF_TOKEN": token,
        "HUGGING_FACE_HUB_TOKEN": token,
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
if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "ERROR: HF_TOKEN was not exported inside the Breeze container!" >&2
  exit 1
fi
echo "Breeze init.sh: HF_TOKEN and AIRFLOW_CONN_HUGGINGFACE_DEFAULT verified (token length: ${#HF_TOKEN})."

LISTENER_FILE="/opt/airflow/airflow-core/tests/unit/listeners/class_listener.py"
if [[ -f "$LISTENER_FILE" ]]; then
  python3 - <<'PATCH_PY'
from pathlib import Path
p = Path("/opt/airflow/airflow-core/tests/unit/listeners/class_listener.py")
text = p.read_text(encoding="utf-8")
text = text.replace("task_instance.note", "getattr(task_instance, 'note', None)")
text = text.replace("dag_run.note", "None")
p.write_text(text, encoding="utf-8")
PATCH_PY
fi
'''
    init_target.write_text(init_script, encoding="utf-8")
    init_target.chmod(0o700)


if __name__ == "__main__":
    main()
