# Hugging Face Airflow system tests

This repository runs the Hugging Face provider system tests from a selected
revision of [`apache/airflow`](https://github.com/apache/airflow), then publishes
a small public history page. Test definitions remain in Airflow; this repository
owns scheduling, credentials, execution, and result summaries.

## What runs

The workflow checks out the selected Airflow ref into a separate directory and
runs `providers/huggingface/tests/system/huggingface/` with Breeze. It reads the
provider test README at runtime and fails clearly if the path has moved. The
default ref is `main`; every result records the resolved Airflow commit SHA.

## Configure GitHub

1. Add a repository secret named `HF_TOKEN_AIRFLOW` only if the current provider test
   README/docstrings require it. Use a dedicated, least-privilege token and
   isolated test organization/resources. The workflow exposes it only to the
   Breeze test step and writes it to Breeze's ignored environment file at
   runtime; a shell trap removes that file on success or failure.
2. Enable GitHub Pages for this repository, using **GitHub Actions** as the
   build and deployment source. [The dashboard deployment workflow](.github/workflows/deploy-dashboard.yml)
   deploys the contents of `site/` after each system-test workflow completes,
   when `site/` changes on `main`, or when manually dispatched.
3. Ensure Actions is allowed to write repository contents and Pages: the
   workflow commits the bounded run history and deploys the dashboard.

Runs are serialized to protect the shared history. The schedule is weekly and
can also be started from **Actions → Run Hugging Face system tests**. Dispatch
accepts an Airflow branch, tag, or commit SHA.

## Local reproduction

Clone Airflow, inspect `providers/huggingface/tests/system/huggingface/README.md`
and relevant test docstrings, then run from the Airflow checkout:

```bash
breeze testing system-tests providers/huggingface/tests/system/huggingface/
```

Provide only credentials actually required by those tests through the local
Breeze environment configuration. Do not commit credentials or publish task
logs. The Actions job adds `--junitxml` via `PYTEST_ADDOPTS`; Breeze/pytest
argument forwarding can vary by Airflow revision. If that revision does not
produce `junit.xml`, the run is still recorded from the command exit code and
the test counts are marked unavailable. Verify report behavior against the
selected Airflow revision before relying on counts.

## Result data

`site/data/runs.json` is summary metadata only: provider, ref and SHA, workflow
URL, timestamps, result, aggregate counts, and duration. It keeps the latest 30
runs. Detailed command output stays in Actions logs; the workflow uploads only
JUnit XML when present. The dashboard at `site/index.html` shows latest status,
last success, recent outcomes, duration, SHA, and run links.

The public history contains no credentials. Review test output handling before
making a repository public, since Actions logs and artifacts follow repository
visibility and retention settings.
