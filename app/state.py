"""Shared state across the agent modules."""

from dataclasses import dataclass, field

from app.config import DEFAULT_WORK_DIR


@dataclass
class AppState:
    work_dir: str = DEFAULT_WORK_DIR
    show_debug: bool = False
    subagent_counter: int = field(default=0, init=False)

    def next_subagent_id(self) -> int:
        """Increment and return the next subagent id."""
        self.subagent_counter += 1
        return self.subagent_counter


__all__ = ["AppState"]
