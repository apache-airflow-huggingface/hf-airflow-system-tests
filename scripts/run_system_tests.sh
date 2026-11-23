#!/usr/bin/env bash
set -eo pipefail
set +e

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
airflow_root="${AIRFLOW_ROOT:-$PWD}"
cd "$airflow_root"

if [[ -z "${HF_TOKEN_AIRFLOW:-}" ]]; then
  echo "::error::HF_TOKEN_AIRFLOW secret is empty or not exposed to this workflow job." >&2
  echo "exit_code=2" >> "$GITHUB_OUTPUT"
  exit 2
fi

# Breeze sources these files from airflow/files/airflow-breeze-config at startup.
mkdir -p files/airflow-breeze-config
export BREEZE_VARIABLES_FILE="$PWD/files/airflow-breeze-config/environment_variables.env"
export BREEZE_INIT_FILE="$PWD/files/airflow-breeze-config/init.sh"
diagnostic_file="$PWD/providers/huggingface/tests/system/huggingface/example_00_hf_connection_diagnostic.py"
if [[ -e "$diagnostic_file" ]]; then
  echo "Refusing to overwrite existing diagnostic path: $diagnostic_file" >&2
  exit 1
fi
cp "$repo_root/scripts/hf_connection_diagnostic.py" "$diagnostic_file"
trap 'rm -f "$BREEZE_VARIABLES_FILE" "$BREEZE_INIT_FILE" "$diagnostic_file"' EXIT
python3 "$repo_root/scripts/prepare_breeze_environment.py"

mapfile -t test_files < <(
  find providers/huggingface/tests/system/huggingface -maxdepth 2 -type f \
    \( -name 'example_*.py' -o -name 'test_*.py' \) | sort
)
if [[ ${#test_files[@]} -eq 0 ]]; then
  echo "No system test files found under providers/huggingface/tests/system/huggingface" >&2
  echo "exit_code=5" >> "$GITHUB_OUTPUT"
  exit 5
fi
echo "Running system tests on: ${test_files[*]}"

AIRFLOW_ROOT_PATH="$PWD" uv run --project dev/breeze --locked --quiet \
  breeze testing system-tests \
    --python "$BREEZE_PYTHON" \
    --github-repository "$BREEZE_GITHUB_REPOSITORY" \
    "${test_files[@]}"
test_status=$?

# Breeze writes JUnit XML at this path inside the container, mounted under ./files.
if [[ -f files/test_result-none-sqlite.xml ]]; then
  cp files/test_result-none-sqlite.xml junit.xml
fi

echo "exit_code=$test_status" >> "$GITHUB_OUTPUT"
exit "$test_status"
