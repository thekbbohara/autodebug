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

**It never stops.** It loops through 10 scan phases, sleeps, then starts over. Kill it when you're done.

## Features

- 🔍 **10-phase deep scan** — recon, dead code, hotspots, dependencies, security, logic bugs, type safety, performance, DB scan, regression check
- 🔁 **Infinite loop** — keeps scanning until you kill it
- 💾 **Context-compaction proof** — writes state to disk, survives AI memory loss
- 📄 **Structured output** — every finding in `debug_output/*.md` with `# Issue` / `# Solution` format
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

# Copy the skill to your CheetahClaws skills directory
mkdir -p ~/.cheetahclaws/skills
cp skills/autodebug.md ~/.cheetahclaws/skills/autodebug.md

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

## How It Survives Context Compaction

AI agents have limited context windows. When context fills up, older messages are lost. AutoDebug solves this:

1. **State file** — `debug_output/.loop_state` tracks current phase, iteration, files scanned
2. **Immediate writes** — every finding is written to disk the moment it's discovered
3. **Recovery protocol** — after compaction, the skill reads `.loop_state` and continues exactly where it left off

## Architecture

```
autodebug/
├── skills/
│   └── autodebug.md          # The CheetahClaws skill definition
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
| `all` (default) | All 10 phases |
| `security` | 1, 5, 7 |
| `performance` | 1, 3, 8, 9 |
| `db` | 1, 9 |
| `dead-code` | 1, 2, 4 |

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-scan`)
3. Commit your changes
4. Push to the branch (`git push origin feature/my-scan`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT — see [LICENSE](LICENSE)
