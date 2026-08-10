#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
uv lock --check
uv run --locked ruff format --check src tests
uv run --locked ruff check src tests
uv run --locked mypy src
uv run --locked pytest -q
uv build
