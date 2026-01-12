"""Tests for Ralph Loop state management."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ralph_loop.state import RalphState


class TestRalphState:
    """Tests for RalphState class."""

    def test_default_state(self):
        """Test creating a default state."""
        state = RalphState(prompt="Test task")

        assert state.active is True
        assert state.iteration == 1
        assert state.max_iterations == 0
        assert state.completion_promise is None
        assert state.prompt == "Test task"

    def test_to_string_and_from_string(self):
        """Test serialization roundtrip."""
        state = RalphState(
            active=True,
            iteration=5,
            max_iterations=10,
            completion_promise="DONE",
            started_at=datetime(2025, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
            prompt="Build a REST API",
        )

        content = state.to_string()
        parsed = RalphState.from_string(content)

        assert parsed is not None
        assert parsed.active == state.active
        assert parsed.iteration == state.iteration
        assert parsed.max_iterations == state.max_iterations
        assert parsed.completion_promise == state.completion_promise
        assert parsed.prompt == state.prompt

    def test_save_and_load(self):
        """Test file save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / ".gemini" / "ralph-loop.local.md"

            state = RalphState(
                prompt="Test task",
                max_iterations=5,
                completion_promise="TEST COMPLETE",
            )
            state.save(state_file)

            loaded = RalphState.from_file(state_file)

            assert loaded is not None
            assert loaded.prompt == "Test task"
            assert loaded.max_iterations == 5
            assert loaded.completion_promise == "TEST COMPLETE"

    def test_increment_iteration(self):
        """Test iteration increment."""
        state = RalphState(
            prompt="Test",
            iteration=1,
            max_iterations=3,
        )

        assert state.increment_iteration() is True
        assert state.iteration == 2

        assert state.increment_iteration() is True
        assert state.iteration == 3

        assert state.increment_iteration() is False
        assert state.iteration == 4
        assert state.active is False

    def test_increment_unlimited(self):
        """Test unlimited iterations."""
        state = RalphState(
            prompt="Test",
            iteration=1,
            max_iterations=0,  # Unlimited
        )

        for _ in range(100):
            assert state.increment_iteration() is True

        assert state.iteration == 101
        assert state.active is True

    def test_should_continue(self):
        """Test should_continue logic."""
        state = RalphState(prompt="Test", active=True)
        assert state.should_continue() is True

        state.active = False
        assert state.should_continue() is False

    def test_check_promise(self):
        """Test promise checking."""
        state = RalphState(
            prompt="Test",
            completion_promise="ALL TESTS PASS",
        )

        # No promise in output
        assert state.check_promise("Some output") is False

        # Promise present
        assert state.check_promise("<promise>ALL TESTS PASS</promise>") is True

        # Case insensitive
        assert state.check_promise("<PROMISE>ALL TESTS PASS</PROMISE>") is True

    def test_check_promise_none(self):
        """Test promise checking when no promise set."""
        state = RalphState(prompt="Test")

        assert state.check_promise("<promise>ANYTHING</promise>") is False

    def test_complete(self):
        """Test completing the loop."""
        state = RalphState(prompt="Test", active=True)
        state.complete()

        assert state.active is False

    def test_from_file_not_found(self):
        """Test loading from non-existent file."""
        state = RalphState.from_file("/nonexistent/path/file.md")
        assert state is None

    def test_status_display(self):
        """Test status display string."""
        state = RalphState(prompt="Test", iteration=5, max_iterations=10, active=True)
        assert "[active]" in state.status_display
        assert "5/10" in state.status_display

        state.active = False
        assert "[stopped]" in state.status_display

        state.max_iterations = 0
        assert "∞" in state.status_display
