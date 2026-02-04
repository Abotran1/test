from __future__ import annotations

from typing import Tuple


class SafetyFilter:
    """Basic safety filter stub.

    Replace this with a production-grade policy or external moderation service.
    """

    def __init__(self) -> None:
        self.blocked_terms = {"harmful", "illegal"}

    def check(self, content: str) -> Tuple[bool, str]:
        lowered = content.lower()
        if any(term in lowered for term in self.blocked_terms):
            return False, "Content violates safety policy."
        return True, ""
