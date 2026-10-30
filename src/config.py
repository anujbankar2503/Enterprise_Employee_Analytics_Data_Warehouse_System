"""Application configuration loaded from the repository's environment file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / "app" / ".env"

load_dotenv(ENV_PATH, override=True)


def database_config(database: str) -> dict[str, object]:
    """Return validated MySQL connection settings for a schema."""
    load_dotenv(ENV_PATH, override=True)
    required = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing database configuration: " + ", ".join(missing) +
            f". Set these values in {ENV_PATH}."
        )
    try:
        port = int(os.environ["DB_PORT"])
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be a whole number.") from exc
    return {
        "host": os.environ["DB_HOST"],
        "port": port,
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": database,
    }