#!/usr/bin/env python3
"""dustbunny — post-session lint + skill-gap analysis agent.

Runs headless Claude Code (the Agent SDK's `claude -p` interface) to lint the
project, analyze the findings, and propose NEW skills or improvements to
existing ones. Writes the proposal to temp/<YYYY-MM-DD_HH-MM-SS>.md, then syncs
the repo to git.

Triggered by launchd (com.saladcode.dustbunny), which the Claude Code SessionEnd
hook kickstarts. Configure with DUSTBUNNY_PROJECT (defaults to ~/Documents/SaladCode).
"""
import datetime
import os
import re
import shutil
import subprocess
import sys

PROJECT = os.environ.get("DUSTBUNNY_PROJECT", os.path.expanduser("~/Documents/SaladCode"))
TEMP = os.path.join(PROJECT, "temp")
CLAUDE = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")

PROMPT = """Use the /lint skill (or ./dustbunny/lint.md if no /lint skill is \
registered) to lint this codebase. Then analyze the lint findings and identify \
potential NEW skills or improvements to EXISTING skills that would prevent or \
auto-fix those findings. Write ONLY the proposal analysis to the file path in \
the $DUSTBUNNY_OUTFILE environment variable, as Markdown, one section per \
proposal:

## <proposal title>
- type: new-skill | skill-improvement
- target: <existing skill name, or 'new'>
- problem: <the lint findings this addresses>
- proposal: <what the skill or change does>

Do not modify any other file. Do not commit."""


def main():
    if not os.path.isdir(PROJECT):
        sys.exit(f"dustbunny: project not found: {PROJECT}")
    os.makedirs(TEMP, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    outfile = os.path.join(TEMP, f"{stamp}.md")
    env = {**os.environ, "DUSTBUNNY_OUTFILE": outfile}

    result = subprocess.run(
        [CLAUDE, "-p", PROMPT, "--permission-mode", "acceptEdits"],
        cwd=PROJECT, env=env, text=True, capture_output=True, timeout=1800,
    )
    if not os.path.exists(outfile):
        # claude didn't write the file — don't lose the run, dump what it said
        with open(outfile, "w") as f:
            f.write(f"# dustbunny analysis {stamp}\n\n"
                    f"(agent fallback — claude did not write the file)\n\n"
                    f"{result.stdout or result.stderr}\n")
    git_sync(stamp, outfile)


def git_sync(stamp, outfile):
    # best-effort: a no-op commit or offline push must not crash the agent.
    # add ONLY our proposal file — a detached background agent must never sweep
    # the user's dirty working tree into a commit/push (was `git add -A`).
    subprocess.run(["git", "add", outfile], cwd=PROJECT, check=False)
    subprocess.run(["git", "commit", "-m", f"dustbunny: post-session lint analysis {stamp}"],
                   cwd=PROJECT, check=False)
    subprocess.run(["git", "push"], cwd=PROJECT, check=False)


def selftest():
    # the only non-trivial logic worth guarding: the timestamp/outfile contract
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    assert STAMP_RE.match(stamp), stamp
    assert os.path.basename(f"{stamp}.md").endswith(".md")
    assert CLAUDE, "claude CLI not found on PATH"
    print("dustbunny selftest: ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
