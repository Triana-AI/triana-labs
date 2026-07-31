#!/usr/bin/env bash

set -euo pipefail

triana_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
triana_project_root="$(cd "${triana_script_dir}/.." && pwd)"
triana_repository_root="$(cd "${triana_project_root}/.." && pwd)"
triana_uv_cache="${UV_CACHE_DIR:-/private/tmp/triana-labs-uv-cache}"
triana_evidence_root="$(mktemp -d /private/tmp/triana-labs-verify.XXXXXX)"
export UV_CACHE_DIR="${triana_uv_cache}"

cd "${triana_repository_root}"
./scripts/verify-governance.sh --working-tree
uv lock --check --project "${triana_project_root}"
uv sync --locked --all-groups --project "${triana_project_root}"

cd "${triana_project_root}"
uv run --locked ruff format --check src tests
uv run --locked ruff check src tests
uv run --locked mypy src
PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest tests -q

triana_frozen_hash="$(
  git ls-files tests/acceptance tests/fixtures \
    | LC_ALL=C sort \
    | xargs shasum -a 256 \
    | shasum -a 256 \
    | awk '{print $1}'
)"
triana_expected_hash="78bd653ffaa2282de7fb094d18e93b4590eaa2e59737d84330160444f985e353"
if [[ "${triana_frozen_hash}" != "${triana_expected_hash}" ]]; then
  echo "frozen acceptance hash mismatch" >&2
  exit 1
fi

mkdir "${triana_evidence_root}/first" "${triana_evidence_root}/second"
set +e
uv run --locked triana traces observe \
  tests/fixtures/mixed_corpus.jsonl \
  --out "${triana_evidence_root}/first/output" \
  >"${triana_evidence_root}/first/receipt.json" \
  2>"${triana_evidence_root}/first/terminal.jsonl"
triana_first_exit=$?
uv run --locked triana traces observe \
  tests/fixtures/mixed_corpus.jsonl \
  --out "${triana_evidence_root}/second/output" \
  >"${triana_evidence_root}/second/receipt.json" \
  2>"${triana_evidence_root}/second/terminal.jsonl"
triana_second_exit=$?
set -e
if [[ "${triana_first_exit}" -ne 10 || "${triana_second_exit}" -ne 10 ]]; then
  echo "canonical mixed corpus did not complete with exit 10" >&2
  exit 1
fi
diff -rq \
  "${triana_evidence_root}/first/output" \
  "${triana_evidence_root}/second/output"

uv build --project "${triana_project_root}" --out-dir "${triana_evidence_root}/dist"
triana_wheels=("${triana_evidence_root}"/dist/*.whl)
if [[ "${#triana_wheels[@]}" -ne 1 ]]; then
  echo "expected exactly one wheel" >&2
  exit 1
fi
uv venv \
  --python "$(tr -d '[:space:]' <"${triana_project_root}/.python-version")" \
  "${triana_evidence_root}/clean-venv"
uv pip install \
  --python "${triana_evidence_root}/clean-venv/bin/python" \
  "${triana_wheels[0]}"
uv run --locked triana --help >"${triana_evidence_root}/source-help.txt"
"${triana_evidence_root}/clean-venv/bin/triana" \
  --help >"${triana_evidence_root}/installed-help.txt"
diff \
  "${triana_evidence_root}/source-help.txt" \
  "${triana_evidence_root}/installed-help.txt"
set +e
"${triana_evidence_root}/clean-venv/bin/triana" \
  traces observe \
  "${triana_project_root}/tests/fixtures/mixed_corpus.jsonl" \
  --out "${triana_evidence_root}/installed-output" \
  >"${triana_evidence_root}/installed-receipt.json" \
  2>"${triana_evidence_root}/installed-terminal.jsonl"
triana_installed_exit=$?
set -e
if [[ "${triana_installed_exit}" -ne 10 ]]; then
  echo "installed wheel did not complete canonical corpus with exit 10" >&2
  exit 1
fi
diff -rq \
  "${triana_evidence_root}/first/output" \
  "${triana_evidence_root}/installed-output"

echo "triana-labs verification passed"
echo "evidence: ${triana_evidence_root}"
