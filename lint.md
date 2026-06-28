---
name: lint
description: Lint a codebase, then analyze the findings to propose new skills or skill improvements that would prevent or auto-fix them. Use when the user asks to "lint", "clean up", "audit the code", or runs automatically post-session via dustbunny.
---

# /lint

Lint the codebase, repair what is safe to repair, and turn recurring lint
findings into **skill proposals** — new skills or improvements to existing ones
that would stop those findings from recurring.

## When to use

- User asks to "lint", "audit", or "clean up" the code
- Before a release or a high-stakes change
- Automatically after a session closes (dustbunny agent)

---

## Workflow

### Step 1: Detect the toolchain

Run whichever linters/formatters the repo already declares — do not install new
ones. Detect by config or manifest:

| Stack | Run if present |
|---|---|
| JS/TS | `npx eslint .`, `npx tsc --noEmit`, `npx prettier --check .` |
| Python | `ruff check .`, `mypy .`, `black --check .` |
| Go | `go vet ./...`, `gofmt -l .` |
| Rust | `cargo clippy`, `cargo fmt --check` |
| Shell | `shellcheck **/*.sh` |
| Markdown | `markdownlint .` |

If no linter is configured, fall back to a structural read: dead files, TODO/FIXME
density, missing error handling at trust boundaries, secrets in source.

### Step 2: Collect findings

Aggregate every finding with: file, rule/category, and a one-line description.
Group by rule so recurring patterns are visible.

### Step 3: Apply safe repairs

Auto-fixable only (`--fix`, formatter writes). Never change logic. Leave anything
ambiguous for review.

### Step 4: Skill-gap analysis  ← the dustbunny step

For each **recurring** finding, ask: *could a skill prevent or auto-fix this?*
Produce one proposal per gap:

```markdown
## <proposal title>
- type: new-skill | skill-improvement
- target: <existing skill name, or 'new'>
- problem: <the lint findings this addresses>
- proposal: <what the skill or change does>
```

Heuristics:
- Same rule firing across many files → a fix/codemod skill.
- A finding that an existing skill *should* have caught → improve that skill.
- A manual repair you just did by hand → a skill so it is automatic next time.

One-off findings are not skill material. Do not invent proposals to fill space.

### Step 5: Write the analysis

Write the proposals (Step 4 only) to the path in `$DUSTBUNNY_OUTFILE` if set,
otherwise to `temp/<YYYY-MM-DD_HH-MM-SS>.md`. Nothing else goes in that file.

### Step 6: Report

```
🔍 Lint Report — <date>
Findings: <N>  ·  Auto-fixed: <N>  ·  Needs review: <N>  ·  Skill proposals: <N>
```

---

## Rules

1. Never install a linter the repo doesn't already use.
2. Auto-fix only what is safe; never alter logic.
3. The analysis file contains proposals only — no fixes, no logs.
4. No proposals for one-off findings.
5. Do not commit; the dustbunny agent handles syncing.
