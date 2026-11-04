"""Public API for simple_time_expression_normalizer.

This module re-exports the names that make up the supported surface of the
library.  The implementation lives in ``core`` so that the package can grow
without changing the import path users depend on.
"""

from .core import normalize, normalize_or_none

__all__ = ["normalize", "normalize_or_none"]
