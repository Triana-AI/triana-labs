from __future__ import annotations

import importlib.util


def test_production_package_exists() -> None:
    assert importlib.util.find_spec("tau2_luna_local") is not None, (
        "the frozen acceptance suite is RED because the tau2_luna_local "
        "production package has not been implemented"
    )
