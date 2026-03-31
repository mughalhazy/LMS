from __future__ import annotations

import os


class SecretConfigurationError(RuntimeError):
    """Domain-specific exception."""


def get_required_secret(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    raise SecretConfigurationError(f"missing_required_secret:{name}")
