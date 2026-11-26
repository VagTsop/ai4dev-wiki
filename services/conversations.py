"""In-memory store for chat conversations.

This is deliberately the simplest thing that works while developing: a dictionary
living inside one process. Two consequences are worth knowing before this ever
reaches a server. Restarting the application loses every conversation, and with
more than one worker process the same conversation id may land on a worker that
has never seen it. A real deployment keeps this in Redis or a database.
"""
import uuid
from dataclasses import dataclass, field


@dataclass
class Conversation:
    id: str
    messages: list[dict] = field(default_factory=list)
    cost_total_usd: float = 0.0

    @property
    def turns(self) -> int:
        return sum(1 for message in self.messages if message["role"] == "user")


_store: dict[str, Conversation] = {}


def create(system: str | None = None) -> Conversation:
    """Start a conversation, optionally pinned to a system prompt."""
    conversation = Conversation(id=uuid.uuid4().hex[:12])
    if system:
        conversation.messages.append({"role": "system", "content": system})
    _store[conversation.id] = conversation
    return conversation


def get(conversation_id: str) -> Conversation | None:
    return _store.get(conversation_id)


def delete(conversation_id: str) -> bool:
    return _store.pop(conversation_id, None) is not None


def ids() -> list[str]:
    return list(_store)
