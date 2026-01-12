"""
Ralph Loop - Iterative development loop extension for Gemini CLI.

A Python implementation of the Ralph technique for AI-assisted
iterative development.
"""

from ralph_loop.loop import (
    cancel_ralph_loop,
    iterate_ralph_loop,
    resume_ralph_loop,
    run_iteration,
    setup_ralph_loop,
)
from ralph_loop.state import HistoryEntry, RalphState

__version__ = "0.2.0"
__all__ = [
    "RalphState",
    "HistoryEntry",
    "setup_ralph_loop",
    "cancel_ralph_loop",
    "run_iteration",
    "iterate_ralph_loop",
    "resume_ralph_loop",
]
