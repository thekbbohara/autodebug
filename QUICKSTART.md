# AutoDebug — Quick Start

## Install

```bash
# Add to your CheetahClaws skills
cp -r skills/ ~/.cheetahclaws/skills/
cp -r scripts/ ~/.cheetahclaws/scripts/
```

## Run

```
/autodebug
```

That's it. It scans your repo, finds bugs, writes findings to `debug_output/`. Loops forever until you kill it.

## Common Flags

| Flag | What it does | Example |
|------|-------------|---------|
| `focus:security` | Only find security bugs | `/autodebug focus:security` |
| `focus:performance` | Only find perf issues | `/autodebug focus:performance` |
| `focus:dead-code` | Only find dead code | `/autodebug focus:dead-code` |
| `focus:db` | Only scan database | `/autodebug focus:db` |
| `target:UserService` | Scope to one class/function/file/dir | `/autodebug target:UserService` |
| `discover-logic` | Infer business rules, ask you to confirm, then find logic bugs | `/autodebug discover-logic` |
| `write-testcase` | Generate test cases for every finding | `/autodebug write-testcase` |
| `min-severity:high` | Only report critical + high findings | `/autodebug min-severity:high` |
| `webhook:url` | POST critical/high findings to a webhook | `/autodebug webhook:https://hooks.slack.com/...` |
| `parallel` | Run scan phases concurrently | `/autodebug parallel` |

Combine them:

```
/autodebug focus:security target:AuthService min-severity:high write-testcase
```

## What It Finds

14 scan phases running in order, then looping:

| # | Phase | Finds |
|---|-------|-------|
| 0 | Business Logic | Infers your domain rules, asks you to confirm *(only with `discover-logic`)* |
| 1 | Recon | Repo health overview |
| 2 | Dead Code | Unreachable functions, unused imports |
| 3 | Hotspots | Complex code likely to have bugs |
| 4 | Dependencies | Circular imports, layer violations |
| 5 | Security | SQL injection, XSS, hardcoded secrets |
| 6 | Logic Bugs | Business rule violations, missing error handling |
| 7 | Type Safety | Type errors, unsafe casts |
| 8 | Performance | N+1 queries, sync blocking, memory leaks |
| 9 | DB Scan | Missing indexes, wrong collation, oversized tables |
| 10 | API Contract | Missing validation, auth, inconsistent responses |
| 11 | Docker | Root user, latest tags, secrets in ENV |
| 12 | Regression | Re-scan, diff from last iteration |
| 13 | Test Cases | Auto-generated tests for findings *(only with `write-testcase`)* |

## Output

All findings go to `debug_output/`:

```
debug_output/
├── 000-business-logic.md   # (if discover-logic)
├── 000-recon.md
├── 001-security-sql-injection.md
├── 002-logic-wrong-discount-order.md
├── 003-dead-code-unused-helper.md
├── .loop_state              # survives context compaction
└── .ignore_list.json       # mark findings as won't-fix
```

Each finding:

```markdown
# [CATEGORY] Short Title

## Issue
- **File**: `src/payments.py:42`
- **Severity**: high
- **Category**: logic
- **Description**: Discount applied after tax, should be before

## Solution
- **Fix**: Move discount calc before tax in `calculateTotal()`
- **Effort**: small
- **Priority**: Must-fix
```

## Ignore Findings

Edit `debug_output/.ignore_list.json`:

```json
{"patterns": [{"category": "dead-code", "file_pattern": "src/legacy/*"}]}
```

## Stop

Just kill it. It loops forever by design.
