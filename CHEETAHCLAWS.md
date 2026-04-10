# CHEETAHCLAWS.md — AutoDebug Project Context

This file is read by CheetahClaws at the start of every session. It contains everything needed to continue working on this project without prior context.

---

## Project Identity

- **Name**: AutoDebug
- **Tagline**: Autonomous, never-stop debugging loop for any codebase
- **License**: MIT (SAIL Lab, UC Berkeley)
- **Repo**: `/home/kb-26/autodebug`
- **Type**: CheetahClaws skill package (not a standalone app)
- **Status**: v0.2 — functional, 2 commits, ready for GitHub deployment

## What AutoDebug Does

AutoDebug is a CheetahClaws skill (`/autodebug`) that runs an infinite 11-phase debugging loop on any repository:
1. Scans for bugs, security vulnerabilities, performance issues, dead code, DB problems
2. Writes structured findings to `debug_output/*.md` (Issue/Solution format)
3. Optionally generates production-grade regression tests (`write-testcase` flag)
4. Loops forever — survives AI context compaction via disk-persisted state
5. Kills only when the user manually stops it

## Architecture

```
autodebug/
├── skills/
│   ├── autodebug.md       # The main skill (184 lines) — loaded by CheetahClaws on /autodebug
│   └── testrules.md       # Test writing rules (410 lines) — loaded by Phase 11 when write-testcase is passed
├── scripts/
│   ├── runner.py          # Autonomous task persistence (129 lines) — registers/tracks loop state on disk
│   ├── repo_audit.py      # Structured audit tracking (196 lines) — finding CRUD + solution plan generator
│   └── test_skill.py      # Validation test suite (7 tests) — CI + manual verification
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
- `arguments`: [focus, scope, write_testcase]
- `tools`: 44 tools listed (jcodemunch MCP + mysql MCP + built-in tools)
- `context`: inline (runs in the current agent, not a sub-agent fork)

**11 Scan Phases**:
| Phase | Name | Focus Modes That Include It |
|-------|------|------------------------------|
| 1 | RECON | all, security, performance, db, dead-code |
| 2 | DEAD CODE | all, dead-code |
| 3 | HOTSPOTS | all, security, performance |
| 4 | DEPENDENCIES | all, dead-code |
| 5 | SECURITY | all, security |
| 6 | LOGIC BUGS | all |
| 7 | TYPE SAFETY | all, security |
| 8 | PERFORMANCE | all, performance |
| 9 | DB SCAN | all, performance, db |
| 10 | REGRESSION | all (loops back to Phase 1 after 5min sleep) |
| 11 | WRITE TEST CASES | all focus modes (only if write-testcase arg passed) |

**Key design decisions**:
- Phase 10 uses SleepTimer(300) then loops back to Phase 1 — this is the "never stop" mechanism
- `.loop_state` file is written after every phase — this is the context compaction recovery mechanism
- Findings are written IMMEDIATELY as individual .md files — not batched — so nothing is lost on crash
- jcodemunch MCP is used for all code analysis, never raw grep — faster and more accurate
- mysql MCP is read-only — never modifies data

**Arguments**:
- `$FOCUS`: security | performance | db | dead-code | all (default: all)
- `$SCOPE`: filesystem path (default: current working directory)
- `$WRITE_TESTCASE`: if "write-testcase" is passed, Phase 11 runs and reads testrules.md

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

**Key design decision**: If the repo has existing tests, follow their conventions. If not, use language defaults (pytest for Python, Jest for TS, Go testing for Go).

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

CLI tool for tracking multi-phase audits with finding management.

**Commands**:
- `repo_audit.py init <id> <repo_path> [name]` — create audit with 10 phase tracking
- `repo_audit.py state <id>` — show full state JSON
- `repo_audit.py phase <id> next` — show next pending phase
- `repo_audit.py phase <id> <phase_key> <status>` — mark phase
- `repo_audit.py finding <id> <category> <severity> <title> <desc> [file] [line] [suggestion]` — add finding
- `repo_audit.py findings <id> [category]` — list findings
- `repo_audit.py plan <id>` — generate prioritized solution_plan.md
- `repo_audit.py list` — list all audits

**Storage**: `audits/<id>/state.json`, `audits/<id>/findings.json`, `audits/<id>/solution_plan.md`

**Note**: The phase tracking in repo_audit.py has 10 phases (1_recon through 10_solution_plan) but autodebug.md has 11 phases (added Phase 11 for test cases). repo_audit.py hasn't been updated yet — see TODO.

### `scripts/test_skill.py` — Validation Suite

7 tests that verify the skill files parse correctly:

| Test | What It Checks |
|------|---------------|
| `test_skill_file_exists` | autodebug.md exists |
| `test_skill_file_parses` | Frontmatter parses, name=autodebug, /autodebug trigger, write_testcase arg |
| `test_required_sections` | All 15 sections present (11 phases + Issue/Solution format + compaction recovery + testrules reference) |
| `test_testrules_file_exists` | testrules.md exists |
| `test_testrules_file_parses` | Frontmatter parses, name=testrules |
| `test_testrules_required_sections` | All 8 steps present (Step 0-7) |
| `test_scripts_exist` | runner.py and repo_audit.py exist |

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
- **Category**: security | bug | performance | dead-code | logic | type-safety | dependency | db
- **Description**: What's wrong and why it matters

## Solution
- **Fix**: Exact code change or approach
- **Effort**: trivial | small | medium | large
- **Priority**: Must-fix | Should-fix | Nice-to-have
```

When `write-testcase` is passed, companion files are written:
- `001-security-sql-injection.md` → `001-security-sql-injection.test.py` (or `.test.ts`, etc.)

## Context Compaction Recovery

The core design principle: **disk is the source of truth, not conversation history**.

Three layers of persistence:
1. **`.loop_state`** (in target repo's `debug_output/`) — current phase, iteration, jcodemunch ID, files scanned
2. **`active_tasks.json`** (in `~/.cheetahclaws/autonomous/`) — task registration, iteration tracking
3. **Individual .md files** (in `debug_output/`) — every finding written immediately, never lost

On wake-up after compaction:
1. Read `debug_output/.loop_state`
2. Resume from the phase marked as current
3. Do NOT restart from Phase 1

## Known Issues & TODO

### Bugs
- `repo_audit.py` has 10 phases but autodebug.md has 11 (Phase 11 test cases not tracked in repo_audit.py state)
- No deduplication — if a finding is written on iteration 1 and the same code is scanned on iteration 2, a duplicate .md may be written
- `runner.py` and `repo_audit.py` are standalone CLIs — not integrated with autodebug.md's flow. The skill prompt tells the AI to use them, but there's no programmatic connection

### Missing Features
- **No auto-fix** — finds problems and writes solutions but doesn't apply fixes (by design — user should review first)
- **No severity threshold** — writes all findings including low/info. Could add `--min-severity` arg
- **No ignore list** — no way to mark findings as "won't fix" to skip on future iterations
- **No notification** — no Slack/Discord/email alerting when critical findings are found
- **No diff between iterations** — Phase 10 regression check is manual, no automated diff of findings between iteration N and N+1
- **No Docker/container scanning** — could add Phase for Dockerfile, docker-compose security
- **No API schema scanning** — could add Phase for OpenAPI/Swagger contract validation
- **No CI integration** — findings are .md files, not JUnit/test format. Could add `--format=junit` for CI consumption
- **No incremental indexing** — re-indexes the whole repo each iteration instead of using `register_edit` + incremental
- **No parallel scanning** — phases run sequentially. Could use CheetahClaws sub-agents for parallel execution

### Design Decisions to Preserve
- Skill file is the single source of truth — scripts are optional tooling
- All MCP tools used must be listed in frontmatter `tools` field
- `context: inline` not `fork` — the loop must run in the main agent to maintain SleepTimer control
- `use_ai_summaries: false` on indexing — keeps indexing fast, the AI does the analysis
- MySQL queries are strictly read-only — never INSERT/UPDATE/DELETE
- No `--fix` flag by design — AutoDebug finds and recommends, never auto-modifies production code

## Git State

- **Branch**: main
- **Commits**: 2
  - `194ca0a` — Initial release
  - `bdf8950` — Add write-testcase feature with production-grade test rules
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
/autodebug                              # Full scan, current directory
/autodebug security                     # Security focus only
/autodebug performance /path/to/repo    # Perf scan on specific repo
/autodebug all . write-testcase         # Full scan + generate regression tests
/autodebug db write-testcase            # DB scan + DB test cases
```

## How to Test

```bash
cd /home/kb-26/autodebug
python3 scripts/test_skill.py
# Expected: 7 tests pass
```

## Coding Rules for This Project

- No comments or docstrings unless logic is genuinely non-obvious
- Only change what was explicitly asked — do not refactor surrounding code
- Keep skill prompt files (autodebug.md, testrules.md) as concise as possible — they get injected into the AI's context window, so every line has a token cost
- Frontmatter field `tools` must list ALL tools the skill might call — if a tool is missing, CheetahClaws won't allow the call
- Test files in `scripts/` are standalone Python scripts, not pytest tests — they use `assert` and print, run with `python3`
- Never add error handling, fallbacks, or validation beyond what is needed
- Never create new abstractions or helpers for one-off operations
