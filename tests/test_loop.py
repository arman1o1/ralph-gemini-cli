"""Tests for Ralph Loop management functions."""

import tempfile
from pathlib import Path

from ralph_loop.loop import cancel_ralph_loop, check_completion, run_iteration, setup_ralph_loop
from ralph_loop.state import RalphState


class TestSetupRalphLoop:
    """Tests for setup_ralph_loop function."""

    def test_basic_setup(self):
        """Test basic loop setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            state = setup_ralph_loop(
                prompt="Build a REST API",
                state_file=state_file,
                quiet=True,
            )

            assert state.active is True
            assert state.iteration == 1
            assert state.prompt == "Build a REST API"
            assert state_file.exists()

    def test_setup_with_options(self):
        """Test setup with all options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            state = setup_ralph_loop(
                prompt="Fix the auth bug",
                max_iterations=10,
                completion_promise="DONE",
                state_file=state_file,
                quiet=True,
            )

            assert state.max_iterations == 10
            assert state.completion_promise == "DONE"


class TestCancelRalphLoop:
    """Tests for cancel_ralph_loop function."""

    def test_cancel_loop(self):
        """Test canceling an active loop."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            # Setup first
            setup_ralph_loop("Test task", state_file=state_file, quiet=True)

            # Cancel
            result = cancel_ralph_loop(state_file=state_file, quiet=True)

            assert result is not None
            assert result.active is False

    def test_cancel_no_loop(self):
        """Test canceling when no loop exists."""
        result = cancel_ralph_loop(state_file="/nonexistent/path.md", quiet=True)
        assert result is None


class TestRunIteration:
    """Tests for run_iteration function."""

    def test_run_iteration(self):
        """Test running an iteration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            setup_ralph_loop("Test task", max_iterations=3, state_file=state_file, quiet=True)

            # Run iterations
            state, should_continue = run_iteration(state_file)
            assert should_continue is True
            assert state.iteration == 2

            state, should_continue = run_iteration(state_file)
            assert should_continue is True
            assert state.iteration == 3

            state, should_continue = run_iteration(state_file)
            assert should_continue is False
            assert state.iteration == 4


class TestCheckCompletion:
    """Tests for check_completion function."""

    def test_check_completion_true(self):
        """Test when completion promise is met."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            setup_ralph_loop(
                "Test task",
                completion_promise="ALL DONE",
                state_file=state_file,
                quiet=True,
            )

            result = check_completion("<promise>ALL DONE</promise>", state_file)
            assert result is True

            # Verify state was updated
            state = RalphState.from_file(state_file)
            assert state.active is False

    def test_check_completion_false(self):
        """Test when completion promise is not met."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            setup_ralph_loop(
                "Test task",
                completion_promise="ALL DONE",
                state_file=state_file,
                quiet=True,
            )

            result = check_completion("Still working...", state_file)
            assert result is False
