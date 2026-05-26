from __future__ import annotations

from pathlib import Path

_REPOSITORY_ROOT = str(Path(__file__).resolve().parents[1])

if _REPOSITORY_ROOT not in __path__:
    __path__.append(_REPOSITORY_ROOT)
