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
uv run --locked ruff format --check src tests examples
uv run --locked ruff check src tests examples
uv run --locked mypy src examples
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

triana_adapter_hash="$(
  cd "${triana_repository_root}"
  git ls-files \
    triana-labs/tests/adapter_acceptance \
    triana-labs/tests/adapter_fixtures \
    | LC_ALL=C sort \
    | xargs shasum -a 256 \
    | shasum -a 256 \
    | awk '{print $1}'
)"
triana_expected_adapter_hash="99cf8455d81aebfb84c30beb9a672bb3f795bb30f67734fd39e11aba4dcde66c"
if [[ "${triana_adapter_hash}" != "${triana_expected_adapter_hash}" ]]; then
  echo "frozen adapter acceptance hash mismatch" >&2
  exit 1
fi

triana_intelligence_hash="$(
  cd "${triana_repository_root}"
  git ls-files \
    triana-labs/tests/intelligence_acceptance \
    triana-labs/tests/intelligence_fixtures \
    | LC_ALL=C sort \
    | xargs shasum -a 256 \
    | shasum -a 256 \
    | awk '{print $1}'
)"
triana_expected_intelligence_hash="2f929a849362f471bf504b741ff2413016c1d3d6132f1a9c0e7073c4c81a77ae"
if [[ "${triana_intelligence_hash}" != "${triana_expected_intelligence_hash}" ]]; then
  echo "frozen intelligence acceptance hash mismatch" >&2
  exit 1
fi

triana_case_factory_content_hash="$(
  cd "${triana_repository_root}"
  git ls-files \
    triana-labs/tests/case_factory_acceptance \
    triana-labs/tests/case_factory_fixtures \
    | LC_ALL=C sort \
    | xargs cat \
    | shasum -a 256 \
    | awk '{print $1}'
)"
triana_expected_case_factory_content_hash="5b0cdb61674dea350bcc35c05e853a69c25d4950ab141422159daa8cb98e3896"
if [[ "${triana_case_factory_content_hash}" != "${triana_expected_case_factory_content_hash}" ]]; then
  echo "frozen case factory acceptance content hash mismatch" >&2
  exit 1
fi

triana_case_factory_file_hash="$(
  cd "${triana_repository_root}"
  git ls-files \
    triana-labs/tests/case_factory_acceptance \
    triana-labs/tests/case_factory_fixtures \
    | LC_ALL=C sort \
    | xargs shasum -a 256 \
    | shasum -a 256 \
    | awk '{print $1}'
)"
triana_expected_case_factory_file_hash="5c5e42090f577004b4f0821f16e52d6dc28fd242bfa27e78229ea36e21b8ff03"
if [[ "${triana_case_factory_file_hash}" != "${triana_expected_case_factory_file_hash}" ]]; then
  echo "frozen case factory acceptance file hash mismatch" >&2
  exit 1
fi

triana_verify_tracked_hash() {
  local path="$1"
  local expected="$2"
  local actual
  actual="$(shasum -a 256 "${triana_repository_root}/${path}" | awk '{print $1}')"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "frozen ${path} hash mismatch" >&2
    exit 1
  fi
}
triana_verify_tracked_hash \
  triana-labs/tests/case_factory_adversarial/test_contract_regressions.py \
  a4140877cb081469a047868cb96a873fcad10b21ebd256177097ec2dc802f943
triana_verify_tracked_hash \
  triana-labs/tests/case_factory_adversarial/test_uncovered_contract_edges.py \
  3d3afc582aafdf45e0cdcbc812987355a50b00170e1d0bf64b2a8bdaeb1d2a07
triana_verify_tracked_hash \
  triana-labs/tests/case_factory_adversarial/test_request_tail_fit.py \
  9e0540e18ea540cb37041570758a69c002a5fc63b49d8cfae16c466f04f6866c

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

triana_verify_hash() {
  local artifact="$1"
  local expected="$2"
  local actual
  actual="$(shasum -a 256 "${triana_evidence_root}/first/output/${artifact}" | awk '{print $1}')"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "canonical ${artifact} hash mismatch" >&2
    exit 1
  fi
}
triana_verify_hash corpus_profile.json 6d6c8d38dae3b7fb4d5580153e7fe1f77f8b9104b6bb28e0f5234c9d30d52146
triana_verify_hash corpus_profile.md 4ede1203e02462d870865abcefdf277c1e24b2bfa16cc5785b42eaf7cc1419c6
triana_verify_hash manifest.json 7a14709fd10373beaa2da842c869988f1d976ddeae34b46501f6d8930fa7e808
triana_verify_hash normalized_traces.jsonl b294d8b0bc9dd5fe8e449015b1d9ef4e72cb815260d88cda394db1bc9fde0447
triana_verify_hash rejected_traces.jsonl c36c32c1adce137a6c6765823fbf271005df64d04547ad9fe17f7ad6c264e98f

uv run --locked python examples/hrai_v2/adapter.py \
  tests/adapter_fixtures/tool_rich_hrai_v2.jsonl \
  --out "${triana_evidence_root}/adapted" \
  --data-class SYNTHETIC \
  >"${triana_evidence_root}/adapter-receipt.json"
uv run --locked triana traces observe \
  "${triana_evidence_root}/adapted/preview_traces.jsonl" \
  --out "${triana_evidence_root}/source-adapter-output" \
  >"${triana_evidence_root}/source-adapter-receipt.json" \
  2>"${triana_evidence_root}/source-adapter-terminal.jsonl"

uv run --locked triana traces observe \
  tests/intelligence_fixtures/structural_traces.jsonl \
  --out "${triana_evidence_root}/source-intelligence-corpus" \
  >"${triana_evidence_root}/source-intelligence-observer-receipt.json" \
  2>"${triana_evidence_root}/source-intelligence-observer-terminal.jsonl"
set +e
uv run --locked triana corpus derive \
  "${triana_evidence_root}/source-intelligence-corpus/manifest.json" \
  --out "${triana_evidence_root}/source-intelligence-output" \
  >"${triana_evidence_root}/source-intelligence-receipt.json" \
  2>"${triana_evidence_root}/source-intelligence-terminal.jsonl"
triana_source_intelligence_exit=$?
set -e
if [[ "${triana_source_intelligence_exit}" -ne 10 ]]; then
  echo "source intelligence did not complete with gaps" >&2
  exit 1
fi

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
"${triana_evidence_root}/clean-venv/bin/python" -c \
  'import sys, zipfile; names = zipfile.ZipFile(sys.argv[1]).namelist(); assert not any("examples/hrai_v2" in name for name in names)' \
  "${triana_wheels[0]}"
uv run --locked triana --help >"${triana_evidence_root}/source-help.txt"
"${triana_evidence_root}/clean-venv/bin/triana" \
  --help >"${triana_evidence_root}/installed-help.txt"
diff \
  "${triana_evidence_root}/source-help.txt" \
  "${triana_evidence_root}/installed-help.txt"
uv run --locked triana cases generate \
  --help >"${triana_evidence_root}/source-case-help.txt"
"${triana_evidence_root}/clean-venv/bin/triana" cases generate \
  --help >"${triana_evidence_root}/installed-case-help.txt"
diff \
  "${triana_evidence_root}/source-case-help.txt" \
  "${triana_evidence_root}/installed-case-help.txt"
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

"${triana_evidence_root}/clean-venv/bin/triana" \
  traces observe \
  "${triana_evidence_root}/adapted/preview_traces.jsonl" \
  --out "${triana_evidence_root}/installed-adapter-output" \
  >"${triana_evidence_root}/installed-adapter-receipt.json" \
  2>"${triana_evidence_root}/installed-adapter-terminal.jsonl"
diff -rq \
  "${triana_evidence_root}/source-adapter-output" \
  "${triana_evidence_root}/installed-adapter-output"

set +e
"${triana_evidence_root}/clean-venv/bin/triana" \
  corpus derive \
  "${triana_evidence_root}/source-intelligence-corpus/manifest.json" \
  --out "${triana_evidence_root}/installed-intelligence-output" \
  >"${triana_evidence_root}/installed-intelligence-receipt.json" \
  2>"${triana_evidence_root}/installed-intelligence-terminal.jsonl"
triana_installed_intelligence_exit=$?
set -e
if [[ "${triana_installed_intelligence_exit}" -ne 10 ]]; then
  echo "installed intelligence did not complete with gaps" >&2
  exit 1
fi
diff -rq \
  "${triana_evidence_root}/source-intelligence-output" \
  "${triana_evidence_root}/installed-intelligence-output"

echo "triana-labs verification passed"
echo "evidence: ${triana_evidence_root}"
