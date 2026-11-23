#!/usr/bin/env python3
"""Write system-test run metadata for the history job."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def dag_ids_by_test_file(airflow_path: Path) -> dict[str, list[str]]:
    """Map each system-test module to the DAG IDs declared in its source."""
    tests_path = airflow_path / "providers/huggingface/tests/system/huggingface"
    mapping: dict[str, list[str]] = {}
    for source_path in sorted((*tests_path.glob("example_*.py"), *tests_path.glob("test_*.py"))):
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        dag_ids: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            if func_name not in {"DAG", "dag"}:
                continue
            dag_id = next(
                (
                    keyword.value.value
                    for keyword in node.keywords
                    if keyword.arg == "dag_id"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ),
                None,
            )
            if dag_id is None and node.args and isinstance(node.args[0], ast.Constant):
                value = node.args[0].value
                dag_id = value if isinstance(value, str) else None
            if dag_id:
                dag_ids.add(dag_id)
        if dag_ids:
            mapping[source_path.stem] = sorted(dag_ids)
    return mapping


def airflow_sha(airflow_path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=airflow_path, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--airflow-path", type=Path, required=True)
    parser.add_argument("--airflow-ref", required=True)
    parser.add_argument("--started-at", default="")
    parser.add_argument("--exit-code", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    metadata = {
        "started_at": args.started_at or now.isoformat(),
        "finished_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exit_code": args.exit_code,
        "airflow_ref": args.airflow_ref,
        "airflow_sha": airflow_sha(args.airflow_path),
        "dag_ids_by_test_file": dag_ids_by_test_file(args.airflow_path),
    }
    args.output.write_text(json.dumps(metadata), encoding="utf-8")


if __name__ == "__main__":
    main()
