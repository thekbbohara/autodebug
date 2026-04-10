<p align="center">
  <img src="docs/logo.svg" alt="AutoDebug" width="120" />
  <h1 align="center">AutoDebug</h1>
  <p align="center"><strong>Autonomous, never-stop debugging loop for any codebase</strong></p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python 3.10+" />
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
    <img src="https://img.shields.io/badge/status-never%20stops-red" alt="Never Stops" />
  </p>
</p>

---

## What Is This?

AutoDebug is a **CheetahClaws skill** that runs an autonomous, infinite debugging loop on any repository. It scans for bugs, security vulnerabilities, performance issues, dead code, and slow database queries — then writes structured findings you can act on.

**It never stops.** It loops through 13 scan phases, sleeps, then starts over. Kill it when you're done.

## Features

- 🔍 **13-phase deep scan** — recon, dead code, hotspots, dependencies, security, logic bugs, type safety, performance, DB scan, API contracts, Docker, regression check, test case generation
- 🔁 **Infinite loop** — keeps scanning until you kill it
- 💾 **Context-compaction proof** — writes state to disk, survives AI memory loss
- 📄 **Structured output** — every finding in `debug_output/*.md` with `# Issue` / `# Solution` format
- 🚫 **Deduplication** — same finding at same location is only written once across iterations
- 🙈 **Ignore list** — mark findings as won't-fix via `debug_output/.ignore_list.json`
- 🎯 **Severity threshold** — pass `high` to skip medium/low findings
- 🔔 **Webhook notifications** — POST critical/high findings to Slack, Discord, or any webhook
- 📊 **Iteration diffing** — compare findings between loop iterations
- ⚡ **Incremental indexing** — only re-index changed files on subsequent iterations
- 🏃 **Parallel scanning** — spawn sub-agents for independent phases
- 🧪 **Test case generation** — pass `write-testcase` to auto-generate production-grade regression tests
- 🗄️ **Database scanning** — MySQL integration (read-only) for missing indexes, oversized tables
- 🐳 **Docker scanning** — Dockerfile security: root user, latest tags, exposed ports, secrets in ENV
- 🔌 **API contract scanning** — missing auth, untyped endpoints, inconsistent responses
- 🔌 **jCodemunch MCP** — indexed code analysis, not raw grep
- ⚡ **Focus modes** — `security`, `performance`, `db`, `dead-code`, or `all`

## Quick Start

### Prerequisites

- [CheetahClaws](https://github.com/sail-berekley-ai/cheetahclaws) installed
- [jCodemunch MCP](https://github.com/nicholasgasior/jcodemunch-mcp) server configured
- (Optional) MySQL MCP server for database scanning

### Install

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/autodebug.git
cd autodebug

# Copy the skill and test rules
mkdir -p ~/.cheetahclaws/skills
cp skills/autodebug.md ~/.cheetahclaws/skills/autodebug.md
cp skills/testrules.md ~/.cheetahclaws/skills/testrules.md

# Copy the autonomous tooling
mkdir -p ~/.cheetahclaws/autonomous
cp scripts/runner.py ~/.cheetahclaws/autonomous/runner.py
cp scripts/repo_audit.py ~/.cheetahclaws/autonomous/repo_audit.py
```

### Run

```
/autodebug                                              # Full scan, current directory
/autodebug security                                     # Security focus only
/autodebug performance /path/to/repo                    # Performance focus on specific repo
/autodebug db                                           # Database scanning only
/autodebug dead-code                                    # Dead code analysis only
/autodebug all . write-testcase                         # Full scan + generate regression tests
/autodebug security . write-testcase                    # Security scan + security test cases
/autodebug all . write-testcase high                   # Full scan + tests, only high+ severity
/autodebug security . write-testcase low https://hooks.slack.com/...  # + webhook notifications
/autodebug all . parallel                               # Parallel sub-agent scanning
```

## Output Format

Every finding is written to `debug_output/NNN-category-title.md`:

```markdown
# [SECURITY] SQL Injection in User Search

## Issue
- **File**: `src/routes/users.ts:47`
- **Severity**: critical
- **Category**: security
- **Description**: String concatenation in SQL query allows injection via `name` parameter

## Solution
- **Fix**: Replace with parameterized query: `db.query('SELECT * FROM users WHERE name = ?', [name])`
- **Effort**: trivial
- **Priority**: Must-fix
```

## Scan Phases

| # | Phase | What It Finds |
|---|-------|---------------|
| 1 | Recon | Repo health, structure overview, initial hotspots |
| 2 | Dead Code | Unreachable symbols, unused imports, dead files |
| 3 | Hotspots | Complex + frequently changed code (bug magnets) |
| 4 | Dependencies | Circular imports, layer violations, fragile coupling |
| 5 | Security | SQL injection, XSS, hardcoded secrets, eval(), unsafe patterns |
| 6 | Logic Bugs | Unhandled exceptions, race conditions, missing awaits |
| 7 | Type Safety | Diagnostics, `Any` types, unsafe casts, missing null checks |
| 8 | Performance | N+1 queries, sync blocking, memory leaks, unbounded arrays |
| 9 | DB Scan | Missing indexes, oversized tables, wrong collations, bad data types |
| 10 | API Contract | Missing auth, untyped endpoints, inconsistent response shapes |
| 11 | Docker | Root user, latest tags, no healthcheck, secrets in ENV |
| 12 | Regression | Snapshot, diff, re-scan, sleep 5 min, loop back to Phase 1 |
| 13 | Test Cases | Auto-generate production-grade regression tests (requires `write-testcase`) |

## Focus Modes

| Focus | Phases Run |
|-------|-----------|
| `all` (default) | All 13 phases, +13 if `write-testcase` |
| `security` | 1, 5, 7, 10, 11, 12, +13 if `write-testcase` |
| `performance` | 1, 3, 8, 9, 12, +13 if `write-testcase` |
| `db` | 1, 9, 12, +13 if `write-testcase` |
| `dead-code` | 1, 2, 4, 12, +13 if `write-testcase` |

## Deduplication

Findings are automatically deduplicated across iterations. The dedup key is `category + title + file_path + line` — the same bug at the same location is only reported once.

The `.loop_state` file tracks a `findings_index` mapping file stems to severities. Before writing any finding, the AI checks this index.

## Ignore List

Mark findings as won't-fix by editing `debug_output/.ignore_list.json`:

```json
{
  "patterns": [
    {"category": "dead-code"},
    {"category": "security", "file_pattern": "src/legacy/*"},
    {"title_pattern": "unused.*helper"}
  ]
}
```

Or use the CLI:
```bash
python3 scripts/repo_audit.py ignore <audit_id> dead-code
python3 scripts/repo_audit.py ignore <audit_id> security "src/legacy/*"
python3 scripts/repo_audit.py unignore <audit_id> 0
```

## Severity Threshold

Pass a severity level as the 4th argument to skip findings below that threshold:

```
/autodebug all . write-testcase high     # Only critical + high
/autodebug security . critical          # Only critical security findings
```

## Webhook Notifications

Pass a webhook URL as the 5th argument to get notified of critical/high findings:

```
/autodebug security . write-testcase low https://hooks.slack.com/services/...
```

The POST payload:
```json
{
  "severity": "critical",
  "category": "security",
  "title": "SQL Injection in User Search",
  "file": "src/routes/users.ts:47",
  "description": "String concatenation in SQL query..."
}
```

## Iteration Diffing

Phase 12 (Regression Check) automatically snapshots findings and diffs between iterations:

- `repo_audit.py snapshot <id> <iteration>` — save current findings
- `repo_audit.py diff <id> 1 2` — compare iteration 1 vs 2
- A `NNN-iteration-diff.md` is written showing new, resolved, and changed findings

## Incremental Indexing

- First iteration: full repo index
- Subsequent iterations: incremental re-index of changed files only
- `register_edit` is called after writing files to keep the index fresh

## Parallel Scanning

Pass `parallel` as the 6th argument to run independent phases concurrently using sub-agents:

```
/autodebug all . parallel
```

Sub-agent assignment:
- **Agent A**: Dead code + Dependencies (Phases 2, 4)
- **Agent B**: Security + Type safety (Phases 5, 7)
- **Agent C**: Hotspots + Performance (Phases 3, 8)
- **Agent D**: DB scan (Phase 9)
- **Agent E**: Docker scan (Phase 11)
- **Main agent**: Recon + Logic + API contract + Regression + Test cases (Phases 1, 6, 10, 12, 13)

## How It Survives Context Compaction

AI agents have limited context windows. When context fills up, older messages are lost. AutoDebug solves this:

1. **State file** — `debug_output/.loop_state` tracks current phase, iteration, audit ID, findings index, files scanned
2. **Immediate writes** — every finding is written to disk the moment it's discovered
3. **Audit tracking** — `repo_audit.py` maintains findings, ignore list, iteration snapshots
4. **Recovery protocol** — after compaction, the skill reads `.loop_state` and continues exactly where it left off

## Architecture

```
autodebug/
├── skills/
│   ├── autodebug.md          # The CheetahClaws skill definition
│   └── testrules.md          # Production-grade test writing rules (loaded by Phase 13)
├── scripts/
│   ├── runner.py             # Autonomous task persistence (survives compaction)
│   ├── repo_audit.py         # Structured audit with finding tracking, dedup, ignore, snapshots
│   └── test_skill.py         # Validation suite (13 tests)
├── docs/
│   ├── logo.svg              # Project logo
│   └── custom-scan.md        # How to customize scan phases
├── .github/
│   └── workflows/
│       └── test.yml           # CI: validate skill file parses correctly
├── LICENSE
├── README.md
└── .gitignore
```

## Configuration

### MySQL Connection

AutoDebug uses whatever MySQL MCP server you have configured in CheetahClaws. It only runs `SELECT` queries — never modifies data.

### Custom Scan Phases

You can modify `skills/autodebug.md` to add, remove, or reorder scan phases. See [docs/custom-scan.md](docs/custom-scan.md).

## Test Case Generation

Pass `write-testcase` as the third argument to auto-generate production-grade regression tests for every finding:

```
/autodebug all . write-testcase         # Full scan + test cases
/autodebug security . write-testcase    # Security scan + security tests
```

### How It Works

1. **Phase 13** scans the repo's existing test patterns first — framework, naming, structure, mocking strategy
2. If the repo has existing tests, new tests follow the same conventions
3. If no tests exist, it picks the best default for the language (pytest for Python, Jest for TS, etc.)
4. For every finding (`001-security-sql-injection.md`), a companion test is written (`001-security-sql-injection.test.py`)
5. Tests reproduce the exact bug — they **fail** if the bug is present, **pass** after the fix

### Test Quality Rules

All generated tests follow the rules in `skills/testrules.md`:

- **Deterministic** — no random, no network, no `datetime.now()`
- **Isolated** — no shared mutable state between tests
- **Fast** — unit tests < 100ms, integration < 5s
- **Named by behavior** — `test_user_login_with_invalid_password_returns_401`, not `testFunction1`
- **AAA pattern** — Arrange, Act, Assert
- **Negative cases** — every happy path test has a failure counterpart
- **Minimal mocking** — only mock external deps, never business logic

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-scan`)
3. Commit your changes
4. Push to the branch (`git push origin feature/my-scan`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT — see [LICENSE](LICENSE)
