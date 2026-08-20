"""Human-readable, sortable identifiers.

Prefixed IDs (`case_01J…`) make logs, URLs, and support conversations far easier
to reason about than bare UUIDs, and the timestamp prefix keeps them k-sortable.
"""

from __future__ import annotations

import secrets
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32: no I, L, O, U


def _encode(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        value, remainder = divmod(value, 32)
        chars.append(_ALPHABET[remainder])
    return "".join(reversed(chars))


def new_id(prefix: str) -> str:
    """Return e.g. `case_01J7ZQK3M8XR4T2VN6WYPB`."""
    timestamp = _encode(int(time.time() * 1000), 10)
    randomness = _encode(secrets.randbits(50), 10)
    return f"{prefix}_{timestamp}{randomness}"
