"""Project-local settings helpers.

This module resolves paths for local data without requiring system-wide
environment changes.
"""

from __future__ import annotations

import os
from pathlib import Path

DATA_DIR_ENV_VAR = "MURDER_SHE_INFERRED_DATA_DIR"
_DOTENV_LOADED = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT.parent / "murder-she-inferred-data"


def _load_project_dotenv() -> None:
    """Load a project-local .env file once, without overriding OS env vars."""
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return

    dotenv_path = PROJECT_ROOT / ".env"
    if not dotenv_path.exists():
        _DOTENV_LOADED = True
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == DATA_DIR_ENV_VAR and value:
            candidate = Path(value).expanduser()
            if not candidate.is_absolute():
                value = str((PROJECT_ROOT / candidate).resolve(strict=False))
        if key:
            os.environ.setdefault(key, value)

    _DOTENV_LOADED = True


def get_data_dir(*, must_exist: bool = True) -> Path:
    """Return the configured data directory path.

    Resolution order:
    1) `MURDER_SHE_INFERRED_DATA_DIR` from process env or local `.env`
    2) Default sibling directory `../murder-she-inferred-data`
    """
    _load_project_dotenv()
    configured = os.environ.get(DATA_DIR_ENV_VAR)
    data_dir = Path(configured).expanduser() if configured else DEFAULT_DATA_DIR
    resolved = data_dir.resolve(strict=False)

    if must_exist and not resolved.exists():
        raise FileNotFoundError(
            f"Data directory does not exist: {resolved}\n"
            f"Set {DATA_DIR_ENV_VAR} in a project-local .env or environment."
        )
    return resolved


def data_path(*parts: str, must_exist: bool = True) -> Path:
    """Build a path under the data directory."""
    path = get_data_dir(must_exist=must_exist).joinpath(*parts)
    if must_exist and not path.exists():
        raise FileNotFoundError(f"Data path does not exist: {path}")
    return path
