from __future__ import annotations

from typing import Protocol


class CurrentUser(Protocol):
    pk: int | None
    is_authenticated: bool
