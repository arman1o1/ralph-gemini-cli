"""
Loop management for Ralph Loop.

Provides functions for setting up, running, and canceling loops.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

from ralph_loop.state import DEFAULT_STATE_FILE, RalphState


def setup_ralph_loop(
    prompt: str,
    max_iterations: int = 0,
    completion_promise: str | None = None,
    state_file: Path | str = DEFAULT_STATE_FILE,
    quiet: bool = False,
) -> RalphState:
    """
    Set up a new Ralph loop.

    Args:
        prompt: The task prompt
        max_iterations: Max iterations (0 = unlimited)
        completion_promise: Phrase that signals completion
        state_file: Path to the state file
        quiet: If True, suppress output

    Returns:
        The created RalphState

    Raises:
        ValueError: If prompt is empty or max_iterations is negative
    """
    # Validate inputs
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    if max_iterations < 0:
        raise ValueError("max_iterations must be non-negative")
    state = RalphState(
        active=True,
        iteration=1,
        max_iterations=max_iterations,
        completion_promise=completion_promise,
        started_at=datetime.now(timezone.utc),
        prompt=prompt,
    )

    state.save(state_file)

    if not quiet:
        _print_activation(state, state_file)

    return state


def cancel_ralph_loop(
    state_file: Path | str = DEFAULT_STATE_FILE,
    quiet: bool = False,
) -> RalphState | None:
    """
    Cancel an active Ralph loop.

    Args:
        state_file: Path to the state file
        quiet: If True, suppress output

    Returns:
        The final state, or None if no loop was active
    """
    state = RalphState.from_file(state_file)

    if state is None:
        if not quiet:
            print("❌ No active Ralph loop found", file=sys.stderr)
            print(f"   State file not found: {state_file}", file=sys.stderr)
        return None

    state.active = False
    state.save(state_file)

    if not quiet:
        print("✅ Ralph loop cancelled")
        print()
        print(f"Final iteration: {state.iteration}")
        print(f"State file: {state_file}")

    return state


def iterate_ralph_loop(
    summary: str = "",
    state_file: Path | str = DEFAULT_STATE_FILE,
    quiet: bool = False,
) -> tuple[RalphState | None, bool]:
    """
    Advance to the next iteration of the loop.

    Args:
        summary: Optional summary of what was accomplished
        state_file: Path to the state file
        quiet: If True, suppress output

    Returns:
        Tuple of (state, can_continue)
    """
    state = RalphState.from_file(state_file)

    if state is None:
        if not quiet:
            print("❌ No active Ralph loop found", file=sys.stderr)
        return None, False

    if not state.should_continue():
        if not quiet:
            print("⏹️ Loop is not active or has reached max iterations")
        return state, False

    can_continue = state.increment_iteration(summary)
    state.save(state_file)

    if not quiet:
        progress = f" ({state.progress_percent}%)" if state.progress_percent is not None else ""
        print(f"📈 Advanced to iteration {state.iteration}{progress}")
        if summary:
            print(f"   Summary: {summary}")
        if not can_continue:
            print("⏹️ Max iterations reached, loop stopped")

    return state, can_continue


def resume_ralph_loop(
    state_file: Path | str = DEFAULT_STATE_FILE,
    quiet: bool = False,
) -> RalphState | None:
    """
    Resume a stopped Ralph loop.

    Args:
        state_file: Path to the state file
        quiet: If True, suppress output

    Returns:
        The resumed state, or None if no loop found
    """
    state = RalphState.from_file(state_file)

    if state is None:
        if not quiet:
            print("❌ No Ralph loop found to resume", file=sys.stderr)
        return None

    if state.active:
        if not quiet:
            print("ℹ️ Loop is already active")
        return state

    if state.resume():
        state.save(state_file)
        if not quiet:
            print("▶️ Ralph loop resumed!")
            print(f"   Continuing from iteration {state.iteration}")
        return state
    else:
        if not quiet:
            print("❌ Could not resume loop")
        return None


def run_iteration(
    state_file: Path | str = DEFAULT_STATE_FILE,
    summary: str = "",
) -> tuple[RalphState | None, bool]:
    """
    Run a single iteration of the loop (backwards compatible).

    This increments the iteration counter and checks if the loop should continue.

    Args:
        state_file: Path to the state file
        summary: Optional summary of work done

    Returns:
        Tuple of (state, should_continue)
    """
    return iterate_ralph_loop(summary=summary, state_file=state_file, quiet=True)


def check_completion(
    output: str,
    state_file: Path | str = DEFAULT_STATE_FILE,
) -> bool:
    """
    Check if the output signals completion.

    Args:
        output: The output text to check
        state_file: Path to the state file

    Returns:
        True if the loop should end (promise fulfilled)
    """
    state = RalphState.from_file(state_file)

    if state is None:
        return True  # No loop to check

    if state.check_promise(output):
        state.complete()
        state.save(state_file)
        return True

    return False


def _print_activation(state: RalphState, state_file: Path | str) -> None:
    """Print activation message."""
    max_iter_display = str(state.max_iterations) if state.max_iterations > 0 else "unlimited"
    promise_display = state.completion_promise if state.completion_promise else "none"

    print("🔄 Ralph loop activated!")
    print()
    print(f"Iteration: {state.iteration}")
    print(f"Max iterations: {max_iter_display}")
    print(f"Completion promise: {promise_display}")
    print()
    print(f"To monitor: cat {state_file}")
    print("To cancel: ralph cancel")
    print()
    print(state.prompt)

    if state.completion_promise:
        print()
        print(f"To complete, output: <promise>{state.completion_promise}</promise>")
        print("Only when the statement is genuinely TRUE!")
