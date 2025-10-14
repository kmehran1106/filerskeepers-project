#!/bin/bash
EXIT=0

echo "=== mypy ==="
uv run mypy .
EXIT=$(($EXIT + $?))

echo "=== ruff ==="
uv run ruff format --check .
EXIT=$(($EXIT + $?))

echo $(tput bold)"EXIT value: ${EXIT}"

exit $EXIT
