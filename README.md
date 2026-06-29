# 🧹 dustbunny

<p align="center">
  <img src="dustbunny.png" alt="dustbunny mascot — a dust bunny holding a blueprint and a hammer" width="320">
</p>

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

**First, download this repo** — don't have Claude rebuild it. Clone it (or grab
the ZIP from GitHub and unzip):

```bash
git clone https://github.com/saladfade/dustbunny.git
```

Then, from **your project root**, paste this into Claude Code (point it at wherever
you downloaded the repo):

> I've downloaded the **dustbunny** repo to `<path/to/dustbunny>`. These files
> already exist — `dustbunny_agent.py`, `lint.md`, and the hooks documented in
> its `README.md`. **Do NOT recreate, rewrite, or regenerate any of them from
> scratch.** Your only job is to sort the existing files into the right places in
> this project and wire up the hooks:
>
> 1. Copy `dustbunny_agent.py` into `dustbunny/` in this project (create that dir
>    plus a `temp/` dir). Leave the file's contents unchanged.
> 2. Copy `lint.md` to `.claude/skills/lint/SKILL.md`, unchanged.
> 3. Add the two hooks (`SessionEnd` + `SessionStart`) to
>    `.claude/settings.json` exactly as written in the downloaded `README.md` —
>    don't invent your own.
> 4. Verify with `python3 dustbunny/dustbunny_agent.py --selftest`.
>
> Use absolute paths throughout. If a file already exists, ask before
> overwriting. Don't edit the contents of the downloaded files — only move them
> and add the hooks. Tell me what you placed where and how to disable it.

---

## Notes & limits

- **Secure delete:** the file is removed with `rm`; macOS dropped `srm` and APFS
  copy-on-write makes true secure-erase unreliable, so this is a plain delete.
- **Cost:** each session close spends one headless Claude run. Disable by
  removing the hooks.
- **Single project:** one hook set targets one repo (`CLAUDE_PROJECT_DIR`).
