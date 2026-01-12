"""
CLI interface for Ralph Loop.

Provides command-line entry points for managing Ralph loops.
"""

import argparse
import sys

from ralph_loop.loop import (
    cancel_ralph_loop,
    iterate_ralph_loop,
    resume_ralph_loop,
    setup_ralph_loop,
)
from ralph_loop.state import RalphState


def main() -> int:
    """Main CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph iterative development loop for Gemini CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ralph start "Build a REST API" --max-iterations 20
  ralph start "Fix auth bug" --completion-promise "ALL TESTS PASS"
  ralph iterate --summary "Added login feature"
  ralph resume
  ralph cancel
  ralph status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new Ralph loop")
    start_parser.add_argument(
        "prompt",
        nargs="+",
        help="Task prompt describing what to accomplish"
    )
    start_parser.add_argument(
        "--max-iterations", "-m",
        type=int,
        default=0,
        metavar="N",
        help="Maximum iterations before auto-stop (0 = unlimited)"
    )
    start_parser.add_argument(
        "--completion-promise", "-p",
        type=str,
        default=None,
        metavar="TEXT",
        help="Phrase that signals task completion"
    )

    # Cancel command
    subparsers.add_parser("cancel", help="Cancel the active Ralph loop")

    # Status command
    subparsers.add_parser("status", help="Show current loop status")

    # Iterate command (NEW)
    iterate_parser = subparsers.add_parser("iterate", help="Advance to next iteration")
    iterate_parser.add_argument(
        "--summary", "-s",
        type=str,
        default="",
        help="Summary of what was accomplished in this iteration"
    )

    # Resume command (NEW)
    subparsers.add_parser("resume", help="Resume a stopped loop")

    # History command (NEW)
    subparsers.add_parser("history", help="Show iteration history")

    args = parser.parse_args()

    if args.command == "start":
        prompt = " ".join(args.prompt)
        if not prompt.strip():
            parser.error("Prompt cannot be empty")
        if args.max_iterations < 0:
            parser.error("--max-iterations must be non-negative")
        try:
            setup_ralph_loop(prompt, args.max_iterations, args.completion_promise)
            return 0
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.command == "cancel":
        result = cancel_ralph_loop()
        return 0 if result else 1

    elif args.command == "status":
        return show_status()

    elif args.command == "iterate":
        state, can_continue = iterate_ralph_loop(summary=args.summary)
        return 0 if state else 1

    elif args.command == "resume":
        result = resume_ralph_loop()
        return 0 if result else 1

    elif args.command == "history":
        return show_history()

    return 1


def start_loop() -> int:
    """Direct entry point for ralph-loop command."""
    parser = argparse.ArgumentParser(
        prog="ralph-loop",
        description="Start a Ralph iterative development loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "prompt",
        nargs="+",
        help="Task prompt"
    )
    parser.add_argument(
        "--max-iterations", "-m",
        type=int,
        default=0,
        metavar="N",
        help="Maximum iterations (0 = unlimited)"
    )
    parser.add_argument(
        "--completion-promise", "-p",
        type=str,
        default=None,
        metavar="TEXT",
        help="Completion phrase"
    )

    args = parser.parse_args()
    prompt = " ".join(args.prompt)

    if not prompt.strip():
        parser.error("Prompt cannot be empty")
    if args.max_iterations < 0:
        parser.error("--max-iterations must be non-negative")

    try:
        setup_ralph_loop(prompt, args.max_iterations, args.completion_promise)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cancel_loop() -> int:
    """Direct entry point for ralph-cancel command."""
    result = cancel_ralph_loop()
    return 0 if result else 1


def show_status() -> int:
    """Show the current loop status."""
    state = RalphState.from_file()

    if state is None:
        print("No active Ralph loop")
        return 0  # Not an error, just informational

    print("📊 Ralph Loop Status")
    print("=" * 40)
    print(f"Status: {'🟢 Active' if state.active else '🔴 Stopped'}")

    # Show iteration with progress
    if state.max_iterations > 0:
        progress = state.progress_percent
        print(f"Iteration: {state.iteration} / {state.max_iterations} ({progress}%)")
    else:
        print(f"Iteration: {state.iteration} (unlimited)")

    if state.completion_promise:
        print(f"Promise: \"{state.completion_promise}\"")
    else:
        print("Promise: none")

    print(f"Started: {state.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    print("Prompt:")
    print("-" * 40)
    print(state.prompt)

    return 0


def show_history() -> int:
    """Show iteration history."""
    state = RalphState.from_file()

    if state is None:
        print("No Ralph loop found")
        return 0

    print("📜 Ralph Loop History")
    print("=" * 40)

    if not state.history:
        print("No history entries yet")
        return 0

    for entry in state.history:
        ts_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"  [{entry.iteration}] {entry.summary} (@{ts_str})")

    print()
    print(f"Current iteration: {state.iteration}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
