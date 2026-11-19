#!/usr/bin/env python3
"""Validate and describe the Hugging Face system tests in an Airflow checkout."""

import ast
from pathlib import Path


ROOT = Path("providers/huggingface/tests/system/huggingface")


def main() -> None:
    if not ROOT.is_dir():
        raise SystemExit(f"Expected provider system-test directory at {ROOT}")

    files = sorted(set(ROOT.rglob("example_*.py")) | set(ROOT.rglob("test_*.py")))
    if not files:
        raise SystemExit(f"No example_*.py or test_*.py files found under {ROOT}")

    print(f"System-test source docstrings at selected Airflow revision ({len(files)} files):")
    for path in files:
        if any(part.startswith(".") for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as error:
            print(f"Could not inspect {path}: {error}")
            continue

        docs = [ast.get_docstring(tree)]
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    docs.append(doc)
        docs = [doc for doc in docs if doc]
        if docs:
            print(f"--- {path} ---")
            print("\n\n".join(docs))


if __name__ == "__main__":
    main()
