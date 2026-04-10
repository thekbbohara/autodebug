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

**It never stops.** It loops through 11 scan phases, sleeps, then starts over. Kill it when you're done.

## Features

- 🔍 **11-phase deep scan** — recon, dead code, hotspots, dependencies, security, logic bugs, type safety, performance, DB scan, regression check, test case generation
- 🔁 **Infinite loop** — keeps scanning until you kill it
- 💾 **Context-compaction proof** — writes state to disk, survives AI memory loss
- 📄 **Structured output** — every finding in `debug_output/*.md` with `# Issue` / `# Solution` format
- 🧪 **Test case generation** — pass `write-testcase` to auto-generate production-grade regression tests for every finding
- 🗄️ **Database scanning** — MySQL integration (read-only) for missing indexes, oversized tables, bad collations
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
/autodebug                              # Full scan, current directory
/autodebug security                     # Security focus only
/autodebug performance /path/to/repo    # Performance focus on specific repo
/autodebug db                           # Database scanning only
/autodebug dead-code                    # Dead code analysis only
/autodebug all . write-testcase         # Full scan + generate regression tests
/autodebug security write-testcase      # Security scan + security test cases
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
| 10 | Regression | Re-scan, sleep 5 min, loop back to Phase 1 |
| 11 | Test Cases | Auto-generate production-grade regression tests for every finding (requires `write-testcase` flag) |

## How It Survives Context Compaction

AI agents have limited context windows. When context fills up, older messages are lost. AutoDebug solves this:

1. **State file** — `debug_output/.loop_state` tracks current phase, iteration, files scanned
2. **Immediate writes** — every finding is written to disk the moment it's discovered
3. **Recovery protocol** — after compaction, the skill reads `.loop_state` and continues exactly where it left off

## Architecture

```
autodebug/
├── skills/
│   ├── autodebug.md          # The CheetahClaws skill definition
│   └── testrules.md          # Production-grade test writing rules (loaded by Phase 11)
├── scripts/
│   ├── runner.py             # Autonomous task persistence (survives compaction)
│   └── repo_audit.py         # Structured audit with finding tracking
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

### Focus Modes

| Focus | Phases Run |
|-------|-----------|
| `all` (default) | All 10 phases, +11 if `write-testcase` |
| `security` | 1, 5, 7, +11 if `write-testcase` |
| `performance` | 1, 3, 8, 9, +11 if `write-testcase` |
| `db` | 1, 9, +11 if `write-testcase` |
| `dead-code` | 1, 2, 4, +11 if `write-testcase` |

## Test Case Generation

Pass `write-testcase` as the third argument to auto-generate production-grade regression tests for every finding:

```
/autodebug all . write-testcase         # Full scan + test cases
/autodebug security . write-testcase    # Security scan + security tests
```

### How It Works

1. **Phase 11** scans the repo's existing test patterns first — framework, naming, structure, mocking strategy
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
