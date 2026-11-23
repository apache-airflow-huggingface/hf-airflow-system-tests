#!/usr/bin/env python3
"""Keep only explicitly approved, non-secret fields in the public run history."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


RUN_ID = re.compile(r"^[0-9]{1,24}$")
SHA = re.compile(r"^(?:[0-9a-f]{7,40}|unknown)$", re.IGNORECASE)
DAG_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,200}$")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T[^\r\n]{1,32}Z$")
RUN_URL_PREFIX = "https://github.com/apache-airflow-huggingface/hf-airflow-system-tests/actions/runs/"


def safe_count(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < 10**9 else None


def sanitize_run(row: Any) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    run_id = str(row.get("run_id", ""))
    if not RUN_ID.fullmatch(run_id):
        return None

    result = row.get("result")
    if not isinstance(result, str) or result not in {"success", "failure"}:
        result = "unknown"
    airflow_sha = row.get("airflow_sha", "unknown")
    if not isinstance(airflow_sha, str) or not SHA.fullmatch(airflow_sha):
        airflow_sha = "unknown"
    airflow_ref = row.get("airflow_ref", "main")
    if not isinstance(airflow_ref, str) or not airflow_ref or len(airflow_ref) > 200 or any(ord(ch) < 32 for ch in airflow_ref):
        airflow_ref = "main"

    workflow_url = f"{RUN_URL_PREFIX}{run_id}"
    supplied_url = row.get("workflow_run_url")
    if supplied_url == workflow_url:
        workflow_url = supplied_url

    tests = row.get("tests")
    clean_tests = None
    if isinstance(tests, dict):
        values = {key: safe_count(tests.get(key)) for key in ("total", "passed", "failed", "skipped")}
        if all(value is not None for value in values.values()):
            clean_tests = values

    dags: dict[str, str] = {}
    raw_dags = row.get("dags", [])
    if isinstance(raw_dags, list):
        for item in raw_dags:
            if not isinstance(item, dict):
                continue
            dag_id, dag_result = item.get("dag_id"), item.get("result")
            if (
                isinstance(dag_id, str)
                and DAG_ID.fullmatch(dag_id)
                and isinstance(dag_result, str)
                and dag_result in {"success", "failure", "skipped"}
            ):
                if dags.get(dag_id) == "failure" or dag_result == "failure":
                    dags[dag_id] = "failure"
                elif dags.get(dag_id) == "success" or dag_result == "success":
                    dags[dag_id] = "success"
                else:
                    dags[dag_id] = "skipped"

    started_at = row.get("started_at", "")
    finished_at = row.get("finished_at", "")
    clean = {
        "provider": "huggingface",
        "airflow_ref": airflow_ref,
        "airflow_sha": airflow_sha,
        "workflow_run_url": workflow_url,
        "started_at": started_at if isinstance(started_at, str) and TIMESTAMP.fullmatch(started_at) else "",
        "finished_at": finished_at if isinstance(finished_at, str) and TIMESTAMP.fullmatch(finished_at) else "",
        "result": result,
        "tests": clean_tests,
        "dags": [{"dag_id": dag_id, "result": dags[dag_id]} for dag_id in sorted(dags)],
        "duration_seconds": safe_count(row.get("duration_seconds")) or 0,
        "run_id": run_id,
    }
    return clean


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("site/data/runs.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("runs", []) if isinstance(payload, dict) else []
    clean_runs = [run for row in rows if (run := sanitize_run(row)) is not None]
    path.write_text(
        json.dumps({"schema_version": 2, "runs": clean_runs}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
