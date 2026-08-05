"""Promotion contracts for repeatable release measurements."""

from .compiler import (
    FrozenMeasurementDefinition,
    compile_measurement,
    execute_frozen_results,
)
from .population import (
    PopulationClassifier,
    classifier_fixture_results,
    compile_population_classifier,
)
from .bundle import (
    BUNDLE_SCHEMA_VERSION,
    build_measurement_bundle,
    bundle_hash,
    execute_bundled_labels,
    execute_native_signal_bundle,
    load_measurement_bundle,
    validate_measurement_bundle,
    write_measurement_bundle,
)
from .native_signal import (
    ABSENT,
    NATIVE_SIGNAL_SCHEMA_VERSION,
    NativeSignalValidationError,
    compile_program,
    evaluate_program,
    validate_program,
)
from .state_signal import (
    STATE_EXECUTOR,
    STATE_SCHEMA_VERSION,
    build_state_schema_profile,
    compute_state_measurement,
)
# NOTE: semantic_runtime is intentionally NOT re-exported here. It imports
# goal_observables (for the judge batching), which imports back into this
# package — importing it at package load time is a circular import. Import it
# directly: `from agentagon.measurement_promotion.semantic_runtime import ...`.

__all__ = [
    "FrozenMeasurementDefinition",
    "compile_measurement",
    "execute_frozen_results",
    "PopulationClassifier",
    "classifier_fixture_results",
    "compile_population_classifier",
    "BUNDLE_SCHEMA_VERSION",
    "build_measurement_bundle",
    "bundle_hash",
    "execute_bundled_labels",
    "execute_native_signal_bundle",
    "load_measurement_bundle",
    "validate_measurement_bundle",
    "write_measurement_bundle",
    "ABSENT",
    "NATIVE_SIGNAL_SCHEMA_VERSION",
    "NativeSignalValidationError",
    "compile_program",
    "evaluate_program",
    "validate_program",
    "STATE_EXECUTOR",
    "STATE_SCHEMA_VERSION",
    "build_state_schema_profile",
    "compute_state_measurement",
]
