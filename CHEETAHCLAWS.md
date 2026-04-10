# CHEETAHCLAWS.md — AutoDebug Project Context

This file is read by CheetahClaws at the start of every session. It contains everything needed to continue working on this project without prior context.

---

## Project Identity

- **Name**: AutoDebug
- **Tagline**: Autonomous, never-stop debugging loop for any codebase
- **License**: MIT (SAIL Lab, UC Berkeley)
- **Repo**: `/home/kb-26/autodebug`
- **Type**: CheetahClaws skill package (not a standalone app)
- **Status**: v0.3 — all bugs fixed, all features implemented

## What AutoDebug Does

AutoDebug is a CheetahClaws skill (`/autodebug`) that runs an infinite 13-phase debugging loop on any repository:
1. Scans for bugs, security vulnerabilities, performance issues, dead code, DB problems, API contract issues, Docker vulnerabilities
2. Writes structured findings to `debug_output/*.md` (Issue/Solution format)
3. Deduplicates findings across iterations
4. Supports ignore lists, severity thresholds, notifications, and parallel scanning
5. Optionally generates production-grade regression tests (`write-testcase` flag)
6. Loops forever — survives AI context compaction via disk-persisted state
7. Kills only when the user manually stops it

## Architecture

```
autodebug/
├── skills/
│   ├── autodebug.md       # The main skill (270 lines) — loaded by CheetahClaws on /autodebug
│   └── testrules.md       # Test writing rules (410 lines) — loaded by Phase 13 when write-testcase is passed
├── scripts/
│   ├── runner.py          # Autonomous task persistence (129 lines) — registers/tracks loop state on disk
│   ├── repo_audit.py      # Structured audit tracking (260 lines) — finding CRUD + dedup + ignore + snapshot/diff
│   └── test_skill.py      # Validation test suite (13 tests) — CI + manual verification
├── docs/
│   ├── logo.svg           # Project logo (red/orange gradient, debug icon)
│   └── custom-scan.md     # Guide for adding/removing/customizing scan phases
├── .github/workflows/
│   └── test.yml           # CI: runs test_skill.py on push/PR
├── CHEETAHCLAWS.md        # THIS FILE — project context for AI sessions
├── README.md              # Full docs with badges, usage, architecture
├── CONTRIBUTING.md         # Contribution guide
├── LICENSE                 # MIT
└── .gitignore
```

## File Deep Dive

### `skills/autodebug.md` — The Core Skill

**Frontmatter fields** (parsed by CheetahClaws skill loader):
- `name`: autodebug
- `triggers`: ["/autodebug"]
- `arguments`: [focus, scope, write_testcase, min_severity, webhook_url, parallel]
- `tools`: 44 tools listed (jcodemunch MCP + mysql MCP + built-in tools)
- `context`: inline (runs in the current agent, not a sub-agent fork)

**13 Scan Phases**:
| Phase | Name | Focus Modes That Include It |
|-------|------|------------------------------|
| 1 | RECON | all, security, performance, db, dead-code |
| 2 | DEAD CODE | all, dead-code |
| 3 | HOTSPOTS | all, security, performance |
| 4 | DEPENDENCIES | all, dead-code |
| 5 | SECURITY SCAN | all, security |
| 6 | LOGIC BUGS | all |
| 7 | TYPE SAFETY | all, security |
| 8 | PERFORMANCE | all, performance |
| 9 | DB SCAN | all, performance, db |
| 10 | API CONTRACT SCAN | all, security |
| 11 | DOCKER SCAN | all, security |
| 12 | REGRESSION CHECK | all (loops back to Phase 1 after 5min sleep) |
| 13 | WRITE TEST CASES | all focus modes (only if write-testcase arg passed) |

**Key design decisions**:
- Phase 12 uses SleepTimer(300) then loops back to Phase 1 — this is the "never stop" mechanism
- `.loop_state` file is written after every phase — this is the context compaction recovery mechanism
- `findings_index` in `.loop_state` tracks all written findings for deduplication
- Findings are written IMMEDIATELY as individual .md files — not batched — so nothing is lost on crash
- jcodemunch MCP is used for all code analysis, never raw grep — faster and more accurate
- mysql MCP is read-only — never modifies data
- Incremental indexing on iteration 2+ via `incremental: true`

**Arguments**:
- `$FOCUS`: security | performance | db | dead-code | all (default: all)
- `$SCOPE`: filesystem path (default: current working directory)
- `$WRITE_TESTCASE`: if "write-testcase" is passed, Phase 13 runs and reads testrules.md
- `$MIN_SEVERITY`: critical | high | medium | low (default: low) — skip findings below threshold
- `$WEBHOOK_URL`: URL to POST critical/high findings to
- `$PARALLEL`: if "parallel" is passed, spawn sub-agents for independent phases

### `skills/testrules.md` — Test Writing Rules

**Structure**: 7 steps with production-grade rules for writing regression tests.

| Step | Content |
|------|---------|
| 0 | Discover existing test patterns from the repo (framework, naming, structure, mocking, fixtures, assertions) |
| 1 | 7 Rules of Production Tests (deterministic, isolated, fast, named by behavior, one behavior per test, no implementation coupling, meaningful failures) |
| 2 | Per-category test templates with code examples (security, logic, performance, dead-code, DB, type safety) |
| 3 | Test file organization (1:1 mirror of source structure, companion .test.* files, standard headers) |
| 4 | Mocking strategy (what to mock vs not, minimal/realistic/explicit/cleaned-up, DB testing strategy) |
| 5 | Assertion quality (bad vs good examples, negative testing for every positive test) |
| 6 | Language-specific patterns with full code examples (Python/pytest, TypeScript/Jest, Go) |
| 7 | 12-point quality checklist before writing any test |

### `scripts/runner.py` — Task Persistence

CLI tool for managing autonomous task state on disk. Survives context compaction.

**Commands**:
- `runner.py register <id> "<desc>" <interval>` — create a task
- `runner.py update <id>` — increment iteration
- `runner.py stop <id>` — mark stopped
- `runner.py pause <id>` / `runner.py resume <id>` — lifecycle
- `runner.py active` — list active tasks
- `runner.py get <id>` — show full task state as JSON
- `runner.py list` — show all tasks

**Storage**: `active_tasks.json` in same directory. Also writes to `loop.log`.

### `scripts/repo_audit.py` — Structured Audit Tracking

CLI tool for tracking multi-phase audits with finding management, dedup, ignore lists, and iteration diffing.

**Commands**:
- `repo_audit.py init <id> <repo_path> [name]` — create audit with 13 phase tracking
- `repo_audit.py state <id>` — show full state JSON
- `repo_audit.py phase <id> next` — show next pending phase
- `repo_audit.py phase <id> <phase_key> <status>` — mark phase
- `repo_audit.py finding <id> <category> <severity> <title> <desc> [file] [line] [suggestion]` — add finding (auto-dedup, auto-ignore)
- `repo_audit.py findings <id> [category] [--min-severity <level>]` — list findings with optional filter
- `repo_audit.py ignore <id> [category] [file_pattern] [title_pattern]` — add ignore pattern
- `repo_audit.py unignore <id> <index>` — remove ignore pattern by index
- `repo_audit.py snapshot <id> <iteration>` — save findings snapshot for iteration N
- `repo_audit.py diff <id> <iter_a> <iter_b>` — compare two iteration snapshots
- `repo_audit.py plan <id>` — generate prioritized solution_plan.md
- `repo_audit.py list` — list all audits

**Storage**: `audits/<id>/state.json`, `audits/<id>/findings.json`, `audits/<id>/ignore_list.json`, `audits/<id>/iteration_N.json`, `audits/<id>/solution_plan.md`

**Dedup**: `add_finding` checks existing findings by `category + title + file_path + line`. If a match exists, the finding is skipped and `None` is returned.

**Ignore list**: `add_finding` checks `ignore_list.json` patterns (category, file_pattern glob, title_pattern regex). Matched findings are skipped.

**Min-severity**: `findings` command accepts `--min-severity <level>` to filter by severity threshold (critical=0, high=1, medium=2, low=3, info=4).

### `scripts/test_skill.py` — Validation Suite

13 tests that verify the skill files parse correctly and repo_audit.py works:

| Test | What It Checks |
|------|---------------|
| `test_skill_file_exists` | autodebug.md exists |
| `test_skill_file_parses` | Frontmatter parses, name=autodebug, all 6 arguments present |
| `test_required_sections` | All 23 sections present (13 phases + Issue/Solution + compaction recovery + testrules reference + dedup + ignore + severity + notifications + incremental + parallel) |
| `test_testrules_file_exists` | testrules.md exists |
| `test_testrules_file_parses` | Frontmatter parses, name=testrules |
| `test_testrules_required_sections` | All 8 steps present (Step 0-7) |
| `test_scripts_exist` | runner.py and repo_audit.py exist |
| `test_repo_audit_has_13_phases` | init creates all 13 phases in state |
| `test_repo_audit_dedup` | Duplicate findings are skipped, different findings are added |
| `test_repo_audit_ignore` | Ignored categories are skipped, non-ignored pass, unignore works |
| `test_repo_audit_snapshot_diff` | Snapshots save, diff detects new findings |
| `test_repo_audit_min_severity` | Severity filter works at critical/high/medium/low thresholds |
| `test_focus_mode_phase_map` | All 5 focus modes present, phases 10-13 numbered correctly |

**Run**: `python3 scripts/test_skill.py` — exits 0 on pass, 1 on fail.

## CheetahClaws Skill System

AutoDebug is a **CheetahClaws skill** — a markdown file with YAML frontmatter that CheetahClaws loads at startup.

**How skills work** (from `cheetahclaws/skill/loader.py`):
1. CheetahClaws scans `~/.cheetahclaws/skills/` (user-level) and `.cheetahclaws/skills/` (project-level) for `.md` files
2. Each file must start with `---` frontmatter containing: name, description, triggers, tools, arguments, etc.
3. The body after the second `---` is the prompt that gets injected when the skill is invoked
4. Arguments are substituted: `$ARGUMENTS` → full args string, `$FOCUS` → first named arg value, etc.
5. `context: inline` means it runs in the current agent; `context: fork` would spawn a sub-agent
6. Project-level skills override user-level skills with the same name (priority: project > user > builtin)

**Skill install paths**:
- User-level: `~/.cheetahclaws/skills/autodebug.md` + `~/.cheetahclaws/skills/testrules.md`
- Project-level: `.cheetahclaws/skills/autodebug.md` (per-repo override)
- Autonomous tools: `~/.cheetahclaws/autonomous/runner.py` + `repo_audit.py`

## Dependencies

### Required
- **CheetahClaws** — the AI agent framework that loads and runs skills
- **jCodemunch MCP** — indexed code analysis server (index_repo, search_symbols, find_dead_code, etc.)

### Optional
- **MySQL MCP** — for Phase 9 DB scanning (read-only queries only)
- **GetDiagnostics** — for Phase 7 type safety scanning (uses pyright/mypy/flake8)

## Output Format

Every finding written to `debug_output/NNN-category-title.md`:

```markdown
# [CATEGORY] Short Title

## Issue
- **File**: `path/to/file:LINE`
- **Severity**: critical | high | medium | low
- **Category**: security | bug | performance | dead-code | logic | type-safety | dependency | db | docker | api
- **Description**: What's wrong and why it matters

## Solution
- **Fix**: Exact code change or approach
- **Effort**: trivial | small | medium | large
- **Priority**: Must-fix | Should-fix | Nice-to-have
```

When `write-testcase` is passed, companion files are written:
- `001-security-sql-injection.md` → `001-security-sql-injection.test.py` (or `.test.ts`, etc.)

## Features

### Deduplication
- `repo_audit.py add_finding` auto-deduplicates by `category + title + file_path + line`
- `.loop_state` → `findings_index` tracks all written finding file stems
- autodebug.md instructs the AI to check findings_index before writing any .md file
- No duplicate findings across iterations

### Ignore List (Won't-Fix)
- `debug_output/.ignore_list.json` — array of patterns with `category`, `file_pattern` (glob), `title_pattern` (regex)
- `repo_audit.py ignore/unignore` commands to manage patterns
- `add_finding` auto-skips matched patterns
- Users can also manually edit the JSON file

### Severity Threshold
- `$MIN_SEVERITY` argument: critical | high | medium | low (default: low)
- Findings below the threshold are skipped during scan phases
- `repo_audit.py findings --min-severity <level>` for CLI filtering

### Notifications
- `$WEBHOOK_URL` argument — POST critical and high severity findings as JSON
- Payload: `{"severity", "category", "title", "file", "description"}`
- Uses `curl` via Bash tool (already in tools list)

### Iteration Diffing
- `repo_audit.py snapshot <id> <iteration>` — saves findings snapshot
- `repo_audit.py diff <id> <iter_a> <iter_b>` — compares two snapshots
- Phase 12 (REGRESSION) auto-snapshots and diffs between iterations
- Writes `NNN-iteration-diff.md` with new/resolved/changed findings

### Incremental Indexing
- Iteration 1: full `index_folder`
- Iteration 2+: `index_folder` with `"incremental": true`
- `register_edit` called after writing files to keep index fresh
- `indexed` flag stored in `.loop_state`

### Parallel Scanning
- `$PARALLEL` argument — spawn sub-agents for independent phases
- Agent A: Phases 2+4 (dead-code + dependencies)
- Agent B: Phases 5+7 (security + type safety)
- Agent C: Phases 3+8 (hotspots + performance)
- Agent D: Phase 9 (DB scan)
- Agent E: Phase 11 (Docker scan)
- Main agent: Phase 1 (recon) + Phase 6 (logic) + Phase 10 (API contract) + Phase 12 (regression) + Phase 13 (test cases)

### Docker/Container Scanning (Phase 11)
- Scans Dockerfiles and docker-compose files
- Checks: running as root, no HEALTHCHECK, ADD vs COPY, latest tags, exposed privileged ports, secrets in ENV
- Included in focus modes: `all`, `security`

### API Contract Scanning (Phase 10)
- Scans route definitions and handler functions
- Checks: missing input validation, missing auth decorators, inconsistent response shapes, untyped request bodies
- Included in focus modes: `all`, `security`

### runner.py/repo_audit.py Integration
- SETUP step 5 initializes audit tracking with `repo_audit.py init` and `runner.py register`
- Each phase calls `repo_audit.py phase <id> <phase_key> in_progress/complete`
- Each finding calls `repo_audit.py finding` (auto-dedup + auto-ignore)
- Phase 12 calls `runner.py update` after each iteration
- Audit ID stored in `.loop_state` for context compaction recovery

## Context Compaction Recovery

The core design principle: **disk is the source of truth, not conversation history**.

Four layers of persistence:
1. **`.loop_state`** (in target repo's `debug_output/`) — current phase, iteration, jcodemunch ID, audit ID, findings_index, files scanned
2. **`active_tasks.json`** (in `~/.cheetahclaws/autonomous/`) — task registration, iteration tracking
3. **`audits/<id>/`** (in scripts/) — findings, ignore list, iteration snapshots, solution plan
4. **Individual .md files** (in `debug_output/`) — every finding written immediately, never lost

On wake-up after compaction:
1. Read `debug_output/.loop_state`
2. Resume from the phase marked as current
3. Use the audit ID from `.loop_state` for repo_audit.py commands
4. Do NOT restart from Phase 1

## Design Decisions to Preserve
- Skill file is the single source of truth — scripts are optional tooling
- All MCP tools used must be listed in frontmatter `tools` field
- `context: inline` not `fork` — the loop must run in the main agent to maintain SleepTimer control
- `use_ai_summaries: false` on indexing — keeps indexing fast, the AI does the analysis
- MySQL queries are strictly read-only — never INSERT/UPDATE/DELETE
- No `--fix` flag by design — AutoDebug finds and recommends, never auto-modifies production code
- Dedup is by `category + title + file_path + line` — same bug at same location should only be reported once
- Ignore list is user-controlled — the AI never adds patterns automatically

## Git State

- **Branch**: main
- **Remote**: Not yet configured (user will deploy to GitHub)

## How to Install (for users)

```bash
git clone https://github.com/YOUR_USERNAME/autodebug.git
cd autodebug
mkdir -p ~/.cheetahclaws/skills
cp skills/autodebug.md ~/.cheetahclaws/skills/autodebug.md
cp skills/testrules.md ~/.cheetahclaws/skills/testrules.md
mkdir -p ~/.cheetahclaws/autonomous
cp scripts/runner.py ~/.cheetahclaws/autonomous/runner.py
cp scripts/repo_audit.py ~/.cheetahclaws/autonomous/repo_audit.py
```

## How to Run

```
/autodebug                                      # Full scan, current directory
/autodebug security                             # Security focus only
/autodebug performance /path/to/repo            # Perf scan on specific repo
/autodebug all . write-testcase                 # Full scan + generate regression tests
/autodebug db write-testcase                    # DB scan + DB test cases
/autodebug all . write-testcase high            # Full scan + tests, only high+ severity
/autodebug security . write-testcase low https://hooks.slack.com/...  # + webhook notifications
/autodebug all . parallel                      # Parallel sub-agent scanning
```

## How to Test

```bash
cd /home/kb-26/autodebug
python3 scripts/test_skill.py
# Expected: 13 tests pass
```

## Coding Rules for This Project

- No comments or docstrings unless logic is genuinely non-obvious
- Only change what was explicitly asked — do not refactor surrounding code
- Keep skill prompt files (autodebug.md, testrules.md) as concise as possible — they get injected into the AI's context window, so every line has a token cost
- Frontmatter field `tools` must list ALL tools the skill might call — if a tool is missing, CheetahClaws won't allow the call
- Test files in `scripts/` are standalone Python scripts, not pytest tests — they use `assert` and print, run with `python3`
- Never add error handling, fallbacks, or validation beyond what is needed
- Never create new abstractions or helpers for one-off operations
