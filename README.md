# 🧹 dustbunny

Post-session housekeeping for [Claude Code](https://claude.com/claude-code) on macOS.

When you close a Claude Code session, dustbunny lints the codebase, analyzes the
findings, and proposes **new skills or skill improvements** that would prevent
them. The proposal is saved to `temp/<timestamp>.md`. The next time you open a
session, Claude reads the latest proposal, asks you `y/n` on each item, acts on
your answers, then deletes the file. The repo is synced to GitHub after each run.

```
session ends ──▶ SessionEnd hook ──▶ python dustbunny_agent.py (nohup, detached)
                                            │
                                            ├─ claude -p  → /lint + skill-gap analysis
                                            ├─ write temp/<timestamp>.md
                                            └─ git add / commit / push
session opens ─▶ SessionStart hook ─▶ inject latest temp/*.md → prompt y/n → rm file
```

The `SessionEnd` hook runs the agent with `nohup … &` so it survives the session
exiting and keeps going while `claude -p` does its work. No launchd, no daemon —
just the hook and the script.

## Contents

| File | What it is |
|---|---|
| `dustbunny_agent.py` | The agent: runs headless `claude -p`, writes the analysis, syncs git |
| `lint.md` | Generalized `/lint` skill (lint → skill-gap analysis), no Obsidian assumptions |
| `README.md` | This file |

## Requirements

- macOS (or Linux), [Claude Code](https://claude.com/claude-code) CLI on your `PATH`
- Python 3 (system `/usr/bin/python3` is fine — no pip packages needed)
- A git repo with a push remote

---

## Manual install

Replace `/path/to/project` with your repo.

**1. Drop the agent in.**
```bash
mkdir -p /path/to/project/dustbunny /path/to/project/temp
cp dustbunny_agent.py /path/to/project/dustbunny/
```

**2. Install the lint skill.**
```bash
mkdir -p /path/to/project/.claude/skills/lint
cp lint.md /path/to/project/.claude/skills/lint/SKILL.md
```

**3. Add the hooks** to `/path/to/project/.claude/settings.json`:
```json
{
  "hooks": {
    "SessionEnd": [
      { "hooks": [ { "type": "command",
        "command": "nohup python3 \"$CLAUDE_PROJECT_DIR/dustbunny/dustbunny_agent.py\" >>/tmp/dustbunny.log 2>&1 &" } ] }
    ],
    "SessionStart": [
      { "hooks": [ { "type": "command",
        "command": "f=$(ls -t \"$CLAUDE_PROJECT_DIR/temp\"/*.md 2>/dev/null | head -1); [ -n \"$f\" ] && printf '<dustbunny-proposals>\\nFor EACH proposal below, ask the user \"Should I create/improve this skill? (y/n)\" and act on the answer. After all are processed, delete this file: %s\\n\\n%s\\n</dustbunny-proposals>\\n' \"$f\" \"$(cat \"$f\")\"" } ] }
    ]
  }
}
```

The agent reads `DUSTBUNNY_PROJECT` (defaults to `~/Documents/SaladCode`); the
hook passes `CLAUDE_PROJECT_DIR` for the path. If your project isn't the default,
set `DUSTBUNNY_PROJECT` in the hook command or the environment.

**4. Test it.**
```bash
python3 /path/to/project/dustbunny/dustbunny_agent.py --selftest   # contract check
python3 /path/to/project/dustbunny/dustbunny_agent.py             # full run
ls /path/to/project/temp/                                          # expect a new .md
```

To disable: remove the two hooks from `settings.json`.

---

## Mega-prompt

Paste this into Claude Code (run from your project root) to set everything up
from scratch:

> Set up **dustbunny** in this repo — a post-session linter that proposes skill
> improvements. Do all of the following:
>
> 1. Create `dustbunny/dustbunny_agent.py`: a Python 3 agent (stdlib only) that
>    (a) reads `DUSTBUNNY_PROJECT` env var, defaulting to this repo's absolute
>    path; (b) makes a `temp/` dir; (c) runs `claude -p` headless with
>    `--permission-mode acceptEdits`, passing a prompt that tells Claude to use
>    the `/lint` skill, then write skill proposals to the file named in
>    `$DUSTBUNNY_OUTFILE`; (d) sets `DUSTBUNNY_OUTFILE` to
>    `temp/<YYYY-MM-DD_HH-MM-SS>.md`; (e) if that file wasn't written, dumps the
>    claude output there as a fallback; (f) runs `git add -A && git commit && git
>    push` best-effort. Add a `--selftest` that asserts the timestamp format and
>    that `claude` is on PATH.
> 2. Create `.claude/skills/lint/SKILL.md`: a `/lint` skill that detects the
>    repo's existing linters (eslint/tsc/ruff/mypy/go vet/clippy/shellcheck —
>    never install new ones), applies only safe auto-fixes, then for each
>    *recurring* finding writes a proposal (`type`, `target`, `problem`,
>    `proposal`) to `$DUSTBUNNY_OUTFILE` or `temp/<timestamp>.md`. Proposals
>    only — no one-off findings, no fixes in that file.
> 3. Add hooks to `.claude/settings.json`: a `SessionEnd` hook that runs
>    `nohup python3 "$CLAUDE_PROJECT_DIR/dustbunny/dustbunny_agent.py"
>    >>/tmp/dustbunny.log 2>&1 &` (detached so it survives the session closing),
>    and a `SessionStart` hook that finds the newest `temp/*.md`, prints it
>    wrapped in `<dustbunny-proposals>` tags with an instruction to ask me `y/n`
>    per proposal and then delete the file.
> 4. Verify with `python3 dustbunny/dustbunny_agent.py --selftest` and one full
>    `python3 dustbunny/dustbunny_agent.py` run. Show me the resulting `temp/*.md`.
>
> Use absolute paths throughout. Tell me what you created and how to disable it.

---

## Notes & limits

- **Secure delete:** the file is removed with `rm`; macOS dropped `srm` and APFS
  copy-on-write makes true secure-erase unreliable, so this is a plain delete.
- **Cost:** each session close spends one headless Claude run. Disable by
  removing the hooks.
- **Single project:** one hook set targets one repo (`CLAUDE_PROJECT_DIR`).
