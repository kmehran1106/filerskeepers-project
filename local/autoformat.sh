#!/bin/bash

echo "=== ruff ==="
uv run ruff check --fix .
uv run ruff format .

echo "Done!"
