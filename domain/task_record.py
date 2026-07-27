from dataclasses import dataclass
from typing import Any


@dataclass
class TaskRecord:
    """A stored task: a server-assigned id paired with the raw {index: {text, language}}
    dict that Task.validate_input already validates - the same shape used everywhere else
    in this app (see CLAUDE.md's note on the task queue's real, dict-based shape)."""

    id: str
    data: dict[Any, Any]
