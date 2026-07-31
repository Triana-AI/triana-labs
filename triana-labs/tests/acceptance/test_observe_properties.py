"""Deterministically seeded boundary properties for portable trace identity."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from conftest import minimal_trace, parse_jsonl, write_jsonl
from hypothesis import HealthCheck, given, seed, settings
from hypothesis import strategies as st

SAFE_ID_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:/@-"
)
SAFE_ID_FIRST_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
)


@seed(2026073101)
@settings(
    max_examples=100,
    deadline=None,
    database=None,
    # The fixture is a stateless subprocess factory; every generated example
    # still receives a fresh TemporaryDirectory and output target below.
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    first=st.sampled_from(tuple(SAFE_ID_FIRST_ALPHABET)),
    tail=st.text(alphabet=SAFE_ID_ALPHABET, min_size=0, max_size=127),
    source_trace_id=st.text(
        alphabet=st.characters(
            blacklist_categories=("Cc", "Cs"),
            blacklist_characters=("\x7f",),
        ),
        min_size=1,
        max_size=80,
    ),
)
def test_valid_identity_values_round_trip_without_reordering(
    first: str,
    tail: str,
    source_trace_id: str,
    run_cli: Any,
    tmp_path: Path,
) -> None:
    trace = minimal_trace(
        trace_id=first + tail,
        source_trace_id=source_trace_id,
        events=[
            {
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": "Synthetic line one.\nSynthetic line two.",
            },
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "",
                "is_final": False,
            },
        ],
    )
    corpus = tmp_path / "property-input.jsonl"
    write_jsonl(corpus, [trace])

    with tempfile.TemporaryDirectory(dir=tmp_path) as temporary:
        output = Path(temporary) / "output"
        result = run_cli("traces", "observe", corpus, "--out", output)

        assert result.returncode == 0
        assert parse_jsonl(output / "normalized_traces.jsonl") == [trace]
