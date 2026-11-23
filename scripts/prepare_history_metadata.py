#!/usr/bin/env python3
"""Write system-test run metadata for the history job."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


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
    }
    args.output.write_text(json.dumps(metadata), encoding="utf-8")


if __name__ == "__main__":
    main()
