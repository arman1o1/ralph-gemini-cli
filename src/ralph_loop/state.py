"""
State management for Ralph Loop.

Handles reading, writing, and updating the loop state file.
"""

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Self

DEFAULT_STATE_FILE = ".gemini/ralph-loop.local.md"


@dataclass
class HistoryEntry:
    """Represents a single iteration history entry."""
    iteration: int
    summary: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RalphState:
    """
    Represents the current state of a Ralph loop.

    Attributes:
        active: Whether the loop is currently active
        iteration: Current iteration number
        max_iterations: Maximum iterations (0 = unlimited)
        completion_promise: Phrase that signals completion
        started_at: When the loop was started
        prompt: The task prompt
        history: List of iteration history entries
    """
    active: bool = True
    iteration: int = 1
    max_iterations: int = 0
    completion_promise: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    prompt: str = ""
    history: list[HistoryEntry] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path | str = DEFAULT_STATE_FILE) -> Self | None:
        """
        Load state from the state file.

        Args:
            path: Path to the state file

        Returns:
            RalphState instance or None if file doesn't exist
        """
        path = Path(path)
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        return cls.from_string(content)

    @classmethod
    def from_string(cls, content: str) -> Self | None:
        """
        Parse state from string content.

        Returns None if content is invalid or corrupt.
        """
        try:
            return cls._parse_content(content)
        except (ValueError, KeyError, IndexError, AttributeError) as e:
            # Log for debugging but don't crash
            print(f"Warning: Failed to parse state file: {e}", file=sys.stderr)
            return None

    @classmethod
    def _parse_content(cls, content: str) -> Self | None:
        """Internal parsing logic."""
        # Normalize line endings
        content = content.replace("\r\n", "\n")

        # Parse YAML frontmatter
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if not match:
            return None

        frontmatter, prompt = match.groups()

        def get_field(name: str, default: str = "") -> str:
            # Match field at start of line in frontmatter
            m = re.search(rf"^{name}:\s*(.*)$", frontmatter, re.MULTILINE)
            return m.group(1).strip() if m else default

        # Parse basic fields
        active = get_field("active") == "true"
        iteration = int(get_field("iteration", "1"))
        max_iterations = int(get_field("max_iterations", "0"))

        # Handle completion promise
        promise_raw = get_field("completion_promise")
        if promise_raw == "null" or not promise_raw:
            completion_promise = None
        else:
            completion_promise = promise_raw.strip('"\'')

        # Parse datetime
        started_at_str = get_field("started_at").strip('"')
        try:
            started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))
        except ValueError:
            started_at = datetime.now(timezone.utc)

        # Parse history
        history = []
        # Find history block
        # Match from "history:" until end of string since it's the last section in frontmatter
        history_match = re.search(r"history:\s*\n(.*)", frontmatter, re.DOTALL)
        if history_match:
            history_text = history_match.group(1)
            for line in history_text.split("\n"):
                line = line.strip()
                if not line or not line.startswith("-"):
                    continue

                # Extract quoted entry: - "..."
                entry_match = re.search(r'-\s*"([^"]+)"', line)
                if not entry_match:
                    continue

                entry_text = entry_match.group(1)
                ts_match = re.search(r"iteration (\d+) @(.+?): (.+)", entry_text)
                if ts_match:
                    iter_num = int(ts_match.group(1))
                    ts_str = ts_match.group(2).strip()
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except ValueError:
                        ts = datetime.now(timezone.utc)
                    history.append(HistoryEntry(
                        iteration=iter_num,
                        summary=ts_match.group(3),
                        timestamp=ts
                    ))
                else:
                    # Fallback to old format: "iteration N: summary"
                    parts = entry_text.split(": ", 1)
                    if len(parts) == 2 and parts[0].startswith("iteration"):
                        try:
                            iter_num = int(parts[0].replace("iteration ", ""))
                            history.append(HistoryEntry(iteration=iter_num, summary=parts[1]))
                        except ValueError:
                            continue

        return cls(
            active=active,
            iteration=iteration,
            max_iterations=max_iterations,
            completion_promise=completion_promise,
            started_at=started_at,
            prompt=prompt.strip(),
            history=history
        )

    def to_string(self) -> str:
        """Convert state to string format."""
        promise_yaml = f'"{self.completion_promise}"' if self.completion_promise else "null"

        # Ensure UTC for started_at
        ts = self.started_at.astimezone(timezone.utc) if self.started_at.tzinfo else self.started_at
        started_at_str = ts.strftime('%Y-%m-%dT%H:%M:%SZ')

        # Build history section
        history_yaml = ""
        if self.history:
            history_yaml = "history:\n"
            for entry in self.history:
                # Ensure UTC for history timestamps
                h_ts = (
                    entry.timestamp.astimezone(timezone.utc)
                    if entry.timestamp.tzinfo
                    else entry.timestamp
                )
                h_ts_str = h_ts.strftime('%Y-%m-%dT%H:%M:%SZ')
                history_yaml += f'  - "iteration {entry.iteration} @{h_ts_str}: {entry.summary}"\n'

        return f"""---
active: {"true" if self.active else "false"}
iteration: {self.iteration}
max_iterations: {self.max_iterations}
completion_promise: {promise_yaml}
started_at: "{started_at_str}"
{history_yaml}---

{self.prompt}
"""

    def save(self, path: Path | str = DEFAULT_STATE_FILE) -> None:
        """Save state to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_string(), encoding="utf-8")

    def increment_iteration(self, summary: str = "") -> bool:
        """Advance to next iteration."""
        if summary:
            self.history.append(HistoryEntry(iteration=self.iteration, summary=summary))

        self.iteration += 1
        if self.max_iterations > 0 and self.iteration > self.max_iterations:
            self.active = False
            return False
        return True

    def should_continue(self) -> bool:
        """Check if loop should continue."""
        if not self.active:
            return False
        if self.max_iterations > 0 and self.iteration > self.max_iterations:
            return False
        return True

    def complete(self, summary: str = "") -> None:
        """Mark as complete."""
        if summary:
            self.history.append(HistoryEntry(iteration=self.iteration, summary=summary))
        self.active = False

    def resume(self) -> bool:
        """Resume a stopped loop."""
        if self.active:
            return False
        if self.max_iterations > 0 and self.iteration > self.max_iterations:
            self.iteration = min(self.iteration, self.max_iterations)
        self.active = True
        return True

    def check_promise(self, output: str) -> bool:
        """Check for completion promise."""
        if not self.completion_promise:
            return False
        pattern = rf"<promise>\s*{re.escape(self.completion_promise)}\s*</promise>"
        return bool(re.search(pattern, output, re.IGNORECASE))

    @property
    def progress_percent(self) -> int | None:
        """Get progress percentage."""
        if self.max_iterations <= 0:
            return None
        return min(100, int((self.iteration / self.max_iterations) * 100))

    @property
    def status_display(self) -> str:
        """Get human-readable status."""
        max_iter = str(self.max_iterations) if self.max_iterations > 0 else "∞"
        status = "active" if self.active else "stopped"
        progress = f" ({self.progress_percent}%)" if self.progress_percent is not None else ""
        return f"[{status}] Iteration {self.iteration}/{max_iter}{progress}"
