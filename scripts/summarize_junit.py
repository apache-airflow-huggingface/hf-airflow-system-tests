#!/usr/bin/env python3
"""Turn a pytest JUnit report and workflow metadata into public-safe history."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def junit_counts(path: Path) -> dict[str, int] | None:
    if not path.is_file():
        return None
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        print(f"Could not parse JUnit report {path}: {exc}", file=sys.stderr)
        return None
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = passed = failed = skipped = 0
    for suite in suites:
        for case in suite.findall("testcase"):
            total += 1
            if case.find("skipped") is not None:
                skipped += 1
            elif case.find("failure") is not None or case.find("error") is not None:
                failed += 1
            else:
                passed += 1
    return {"total": total, "passed": passed, "failed": failed, "skipped": skipped}


def build_record(args: argparse.Namespace) -> dict[str, Any]:
    started, finished = parse_time(args.started_at), parse_time(args.finished_at)
    counts = junit_counts(Path(args.junit))
    exit_code = int(args.exit_code)
    result = "success" if exit_code == 0 else "failure"
    return {
        "provider": "huggingface",
        "airflow_ref": args.airflow_ref,
        "airflow_sha": args.airflow_sha,
        "workflow_run_url": args.run_url,
        "started_at": started.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "finished_at": finished.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "result": result,
        "tests": counts,
        "duration_seconds": max(0, int((finished - started).total_seconds())),
        "run_id": args.run_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", default="junit.xml")
    parser.add_argument("--output", required=True)
    parser.add_argument("--history")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--airflow-ref")
    parser.add_argument("--airflow-sha")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--started-at")
    parser.add_argument("--finished-at")
    parser.add_argument("--exit-code", type=int)
    args = parser.parse_args()

    if args.metadata:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        args.airflow_ref = metadata["airflow_ref"]
        args.airflow_sha = metadata["airflow_sha"]
        args.started_at = metadata["started_at"]
        args.finished_at = metadata["finished_at"]
        args.exit_code = metadata["exit_code"]

    required_values = (
        "airflow_ref",
        "airflow_sha",
        "started_at",
        "finished_at",
        "exit_code",
    )
    missing = [name for name in required_values if getattr(args, name) is None]
    if missing:
        missing_flags = ", ".join("--" + name.replace("_", "-") for name in missing)
        parser.error(f"provide --metadata or all required fields (missing: {missing_flags})")

    record = build_record(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if args.history:
        history_path = Path(args.history)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
            runs = history.get("runs", []) if isinstance(history, dict) else []
        except (OSError, json.JSONDecodeError):
            runs = []
        runs = [record] + [row for row in runs if row.get("run_id") != record["run_id"]]
        history_path.write_text(
            json.dumps({"schema_version": 1, "runs": runs[: max(args.limit, 1)]}, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Recorded {record['result']} run; JUnit counts: {record['tests']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
