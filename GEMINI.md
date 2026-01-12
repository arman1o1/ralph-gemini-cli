# Ralph in Gemini CLI Extension (Python)

This extension enables **Ralph Loops**: self-referential, iterative development cycles where Gemini improves its work until completion.

> [!IMPORTANT]
> **Core Principle**: When a user initiates a Ralph loop, you are entering an autonomous agentic mode. You must strictly follow the state management protocol defined below.

## 🔄 Command Protocol

### `/ralph-loop <prompt>`

**Trigger**: User starts a new task loop.

**Action Reference**:

1. **Initialize State**:
   Run the following command using the `Shell` tool.

   > [!WARNING]
   > Do NOT use `run_terminal_command` or other variants. Use `Shell` with the exact string below.

   ```bash
   python -m ralph_loop.cli start "<prompt>"
   ```

2. **Read State**:
   Read the file `.gemini/ralph-loop.local.md` to confirm the loop is active.

3. **Execute Task**:
   Begin working on the user's prompt (creating files, writing code, etc.).

4. **Iterate**:
   After making a unit of progress, advance the loop.

   ```bash
   python -m ralph_loop.cli iterate --summary "Brief description of what you did"
   ```

5. **Loop**:
   Repeat steps 3 and 4 until the task is complete or max iterations are reached.

---

### `/ralph-iterate <summary>`

**Trigger**: User manually advances the loop.

**Action Reference**:

```bash
python -m ralph_loop.cli iterate --summary "<summary>"
```

---

### `/ralph-history`

**Trigger**: User wants to see what happened.

**Action Reference**:

```bash
python -m ralph_loop.cli history
```

---

### `/ralph-status`

**Trigger**: User checks loop status.

**Action Reference**:

```bash
python -m ralph_loop.cli status
```

---

### `/ralph-cancel`

**Trigger**: User stops the loop.

**Action Reference**:

```bash
python -m ralph_loop.cli cancel
```

## 🧠 Model Instructions

### State File (`.gemini/ralph-loop.local.md`)

This file is the **Source of Truth**.

- **Always read it** if you lose context.
- **Never edit it contextually**. Only modify it via the `ralph_loop.cli` commands.

### Completion Promise

If the user sets a `--completion-promise` (e.g., "ALL TESTS PASS"), you must **verify** this condition is met before stopping.

When the condition is met, output the promise EXACTLY as follows to signal the CLI to stop:

```xml
<promise>THE_PROMISE_TEXT</promise>
```

> [!CAUTION]
> Do NOT output the promise tag unless the condition is genuinely true. False completions break the trust in the loop.

### Tool Usage Rules

1. **Shell Tool ONLY**: For all `python -m ralph_loop.cli` commands, use the `Shell` tool.
2. **No Markdown Rendering**: When running CLI commands, do not try to render the output yourself; just pipe the command result to the user if requested.
3. **Conciseness**: Keep iteration summaries short (under 100 chars preferred).

## 🐛 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| **Command Rejected** | Check that you are using the `Shell` tool and not `EditFile`. |
| **State Corrupt** | Run `ralph cancel` to reset, then `ralph start`. |
| **Infinite Loop** | Check `max_iterations` in status. If 0 (unlimited), suggest the user manually cancel if stuck. |
