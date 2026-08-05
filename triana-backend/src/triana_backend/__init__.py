"""Triana backend package.

The package is intentionally split around ports: API and workflow code do not
open database sessions or access artifact bytes directly.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
