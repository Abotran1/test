from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import uuid


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MemoryStore:
    """In-memory conversation store with simple session management.

    This is intentionally small and easy to swap with a database-backed store.
    """

    def __init__(self, max_history_messages: int = 30) -> None:
        self._sessions: Dict[str, List[Message]] = {}
        self._max_history_messages = max_history_messages

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    def get_messages(self, session_id: str) -> List[Message]:
        return list(self._sessions.get(session_id, []))

    def append_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(Message(role=role, content=content))
        self._trim_history(session_id)

    def reset_session(self, session_id: str) -> None:
        self._sessions[session_id] = []

    def _trim_history(self, session_id: str) -> None:
        messages = self._sessions.get(session_id, [])
        if len(messages) > self._max_history_messages:
            self._sessions[session_id] = messages[-self._max_history_messages :]
