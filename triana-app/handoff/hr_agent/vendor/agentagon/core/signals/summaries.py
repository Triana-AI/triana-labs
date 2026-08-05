"""Helpers for building and reading signal summaries."""

from __future__ import annotations

from dataclasses import replace

from agentagon.core.types.signals import Signal, SignalSummaries, SignalValue


SESSION_OVERALL_ENTITY_ID = "session:overall"
COHORT_OVERALL_ENTITY_ID = "cohort:overall"

SignalObservationMap = dict[tuple[str, str], list[SignalValue]]


def build_signal_summaries(
    signals: tuple[Signal, ...],
    *,
    include_session_overall: bool,
    include_cohort_overall: bool,
) -> SignalSummaries:
    observations: SignalObservationMap = {}
    for signal in signals:
        for entity_id in entity_ids_for_summary(
            signal.value,
            include_session_overall=include_session_overall,
            include_cohort_overall=include_cohort_overall,
        ):
            observations.setdefault((entity_id, signal.name), []).append(signal.value)
    return _summaries_from_observations(observations)


def entity_ids_for_summary(
    value: SignalValue,
    *,
    include_session_overall: bool,
    include_cohort_overall: bool,
) -> tuple[str, ...]:
    entity_ids: list[str] = []
    seen: set[str] = set()
    for observation in getattr(value, "observations", ()):
        for ids in observation.entities.values():
            for entity_id in sorted(ids):
                if entity_id == SESSION_OVERALL_ENTITY_ID and not include_session_overall:
                    continue
                if entity_id == COHORT_OVERALL_ENTITY_ID and not include_cohort_overall:
                    continue
                if entity_id in seen:
                    continue
                entity_ids.append(entity_id)
                seen.add(entity_id)
    return tuple(entity_ids)


def summary_stats(summaries: SignalSummaries) -> dict[str, dict[str, object]]:
    return {
        entity_id: {
            signal_name: value.get_stats()
            for signal_name, value in signal_summaries.items()
        }
        for entity_id, signal_summaries in summaries.items()
    }


def get_summary_stats(
    summaries: SignalSummaries,
    entity_id: str,
    signal_name: str,
) -> object | None:
    value = summaries.get(entity_id, {}).get(signal_name)
    return None if value is None else value.get_stats()


def _summaries_from_observations(
    observations: SignalObservationMap,
) -> SignalSummaries:
    summaries: SignalSummaries = {}
    for (entity_id, signal_name), values in observations.items():
        single_observation_values = tuple(
            _value_for_observation(value, observation)
            for value in values
            for observation in getattr(value, "observations", ())
            if any(entity_id in entity_ids for entity_ids in observation.entities.values())
        )
        if not single_observation_values:
            continue
        summaries.setdefault(entity_id, {})[signal_name] = type(
            single_observation_values[0]
        ).aggregate(single_observation_values)
    return summaries


def _value_for_observation(value: SignalValue, observation: object) -> SignalValue:
    return replace(value, observations=(observation,))


__all__ = [
    "COHORT_OVERALL_ENTITY_ID",
    "SESSION_OVERALL_ENTITY_ID",
    "build_signal_summaries",
    "entity_ids_for_summary",
    "get_summary_stats",
    "summary_stats",
]
