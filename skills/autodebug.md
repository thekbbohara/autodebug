---
name: autodebug
description: Autonomous never-stop debugging loop — scans entire repo for bugs, security issues, performance problems, slow DB queries. Writes findings to debug_output/*.md. Loops forever until manually killed.
triggers: ["/autodebug"]
tools: [mcp__jcodemunch__index_folder, mcp__jcodemunch__resolve_repo, mcp__jcodemunch__get_repo_health, mcp__jcodemunch__get_repo_outline, mcp__jcodemunch__suggest_queries, mcp__jcodemunch__find_dead_code, mcp__jcodemunch__get_dead_code_v2, mcp__jcodemunch__get_hotspots, mcp__jcodemunch__get_dependency_cycles, mcp__jcodemunch__get_layer_violations, mcp__jcodemunch__get_coupling_metrics, mcp__jcodemunch__search_text, mcp__jcodemunch__search_symbols, mcp__jcodemunch__get_file_outline, mcp__jcodemunch__get_symbol_source, mcp__jcodemunch__get_symbol_complexity, mcp__jcodemunch__get_call_hierarchy, mcp__jcodemunch__get_blast_radius, mcp__jcodemunch__get_class_hierarchy, mcp__jcodemunch__get_file_content, mcp__jcodemunch__find_importers, mcp__jcodemunch__find_references, mcp__jcodemunch__check_references, mcp__jcodemunch__get_context_bundle, mcp__jcodemunch__plan_turn, mcp__jcodemunch__register_edit, mcp__mysql__mysql_query, Read, Write, Edit, Bash, Glob, Grep, GetDiagnostics, SleepTimer, TaskCreate, TaskUpdate, TaskList, Skill]
when-to-use: Use when user says "/autodebug", "autodebug", "run autodebug", "debug entire repo", "find all bugs". User can optionally specify focus areas as arguments.
argument-hint: [focus: security|performance|db|dead-code|all] [scope: path-or-all] [write-testcase]
arguments: [focus, scope, write_testcase]
context: inline
---

You are now in **AUTODEBUG MODE** — an autonomous, never-stop debugging loop.

## MISSION
Scan the current repo (or $SCOPE) continuously for bugs, security issues, performance problems, and slow DB queries. Write EVERY finding to `debug_output/*.md` using the exact format below. NEVER pause, NEVER ask for confirmation, NEVER stop until the user manually kills you.

## ARGUMENTS
- $FOCUS — What to focus on: `security`, `performance`, `db`, `dead-code`, or `all` (default: `all`)
- $SCOPE — Path to scan (default: current working directory)
- $WRITE_TESTCASE — If `write-testcase` is passed, generate production-grade test cases for every finding. Read `testrules.md` for full test writing rules.

## SETUP (do this FIRST — always)

1. Determine the repo path: use `$SCOPE` if provided, otherwise use the current working directory.
2. Check if repo is indexed via jcodemunch: `resolve_repo { "path": "<repo_path>" }`
   - If not indexed: `index_folder { "path": "<repo_path>", "use_ai_summaries": false }`
3. Create `debug_output/` directory inside the repo if it doesn't exist.
4. Write a `.loop_state` file to `debug_output/.loop_state` containing:
   - Mission description
   - Repo path and jcodemunch ID
   - Current phase and iteration number
   - Files scanned so far
   - This file is your SOURCE OF TRUTH after context compaction
5. **If $WRITE_TESTCASE is passed**: Read `skills/testrules.md` (or `.cheetahclaws/skills/testrules.md`) in full. This file contains ALL rules for writing production-grade test cases. You MUST follow those rules for every test you write. Before writing any test, complete Step 0 from testrules.md: discover the repo's existing test patterns by scanning test directories, reading existing test files, and extracting the framework, naming, structure, mocking strategy, and assertion style used.

## OUTPUT FORMAT (MANDATORY — every .md file MUST follow this)

```markdown
# [CATEGORY] Short Title

## Issue
- **File**: `path/to/file.py:LINE`
- **Severity**: critical | high | medium | low
- **Category**: security | bug | performance | dead-code | logic | type-safety | dependency | db
- **Description**: What's wrong and why it matters

## Solution
- **Fix**: Exact code change or approach
- **Effort**: trivial | small | medium | large
- **Priority**: Must-fix | Should-fix | Nice-to-have
```

## SCAN PHASES (execute in order, then loop back to Phase 1)

### Phase 1: RECON
- `get_repo_health` → overall stats, dead code %, hotspots
- `get_repo_outline` → structure, languages
- `suggest_queries` → hot areas to investigate
- Write `debug_output/000-recon.md` with repo health summary
- Mark phase complete in `.loop_state`

### Phase 2: DEAD CODE
- `find_dead_code` (granularity=symbol, min_confidence=0.5, include_tests=true)
- `get_dead_code_v2` (min_confidence=0.5)
- For each dead symbol: write individual finding .md file
- Skip this phase if $FOCUS is `security` or `performance`

### Phase 3: HOTSPOTS (bug-risk code)
- `get_hotspots` → complex + frequently changed code
- `get_symbol_complexity` on top results
- Look for: god functions, deep nesting, too many params
- Write findings for anything medium complexity or above
- Skip if $FOCUS is `security`

### Phase 4: DEPENDENCIES
- `get_dependency_cycles` → circular imports
- `get_layer_violations` → architecture breaks
- `get_coupling_metrics` on key files → unstable modules
- Skip if $FOCUS is `security` or `performance`

### Phase 5: SECURITY SCAN
- `search_text` with regex for: `password|secret|api_key|token|eval\(|exec\(|__import__|pickle\.load|yaml\.load|subprocess|os\.system|dangerouslySetInnerHTML|innerHTML`
- `search_text` for: hardcoded URLs, inline SQL, string concatenation in queries
- Check `.env.example`, config files for exposed defaults
- Check for: XSS vectors, unsafe deserialization, missing auth checks, SQL injection
- Write each finding immediately as a separate .md file
- Skip if $FOCUS is `performance` or `dead-code`

### Phase 6: LOGIC BUGS
- Read source of hotspot files using `get_symbol_source`
- Look for: unhandled exceptions, race conditions, missing await/error handling
- Pattern match: `.then(` without `.catch`, bare `except:`, missing `try/finally`
- Off-by-one in loops, missing null/None checks
- Write each finding immediately
- Skip if $FOCUS is `security` or `dead-code`

### Phase 7: TYPE SAFETY
- `GetDiagnostics` on key source files
- `search_text` for `Any`, `# type: ignore`, `as Any`, `cast(`
- Write findings for type issues that could cause runtime errors
- Skip if $FOCUS is `security` or `performance`

### Phase 8: PERFORMANCE
- `search_text` for: N+1 patterns, sync blocking calls, unbounded arrays/lists
- Check: missing pagination, unbounded DB queries, full table scans
- Look for: list.append in hot loops, string concat in loops, unnecessary deepcopy
- Write findings
- Skip if $FOCUS is `security` or `dead-code`

### Phase 9: DB SCAN (MySQL — read-only)
- `mysql_query` → list all schemas: `SELECT DISTINCT table_schema FROM information_schema.tables WHERE table_schema NOT IN ('mysql','information_schema','performance_schema','sys')`
- For each schema: list large tables with row counts and sizes
- Check for: tables with ZERO indexes (besides PRIMARY), redundant indexes, missing composite indexes
- Check for: `latin1_swedish_ci` collation (should be `utf8mb4`), wrong data types (varchar for dates, float for money)
- Check for: oversized tables without partitioning, tables > 1M rows with only PK index
- Run: `SHOW INDEX FROM <table>` for the biggest tables
- Write each DB finding as a separate .md file with `category: db`
- Skip if $FOCUS is `dead-code` or `security`

### Phase 10: REGRESSION CHECK
- Re-read source of previously scanned files
- Check if any new issues appeared since last scan
- Update `.loop_state` with iteration number
- Set SleepTimer for 300 seconds (5 minutes)
- When timer fires, START OVER from Phase 1

### Phase 11: WRITE TEST CASES (only if $WRITE_TESTCASE is passed)
- This phase runs AFTER all other phases complete each iteration
- **Read `skills/testrules.md`** — it contains the complete rules for writing production-grade tests
- Before writing ANY test, complete Step 0 from testrules.md:
  1. `get_file_tree` with `path_prefix="tests/"` or `path_prefix="__tests__/"` — discover test directory structure
  2. `get_file_outline` on 3-5 existing test files — extract framework, naming, structure
  3. `get_symbol_source` on representative test functions — understand mocking, assertions, fixtures
  4. Record the discovered patterns in `.loop_state` so you don't re-discover after compaction
- For EACH finding written in phases 2-9, write a companion test file:
  - `001-security-sql-injection.md` → `001-security-sql-injection.test.py` (or `.test.ts`, etc.)
  - Test must reproduce the exact bug found
  - Test must FAIL if the bug is present, PASS after fix
  - Follow the repo's existing test patterns (framework, naming, structure, mocking)
  - If NO existing tests found, use language defaults from testrules.md §0.3
  - Every test file gets the standard header from testrules.md §3.3
- Write tests to `debug_output/` alongside the finding .md files
- If the finding .md file already has a companion `.test.*` file, skip it (already covered)
- Never write tests for findings you haven't confirmed through source code analysis

## FOCUS MODE PHASE MAP

| Focus | Phases |
|-------|--------|
| `all` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, [11 if write-testcase] |
| `security` | 1, 5, 7, [11 if write-testcase] |
| `performance` | 1, 3, 8, 9, [11 if write-testcase] |
| `db` | 1, 9, [11 if write-testcase] |
| `dead-code` | 1, 2, 4, [11 if write-testcase] |

## CRITICAL RULES

1. **NEVER pause** — keep scanning, keep writing
2. **NEVER ask for confirmation** — just do it
3. **NEVER stop** — loop forever until killed
4. **Write findings IMMEDIATELY** — don't batch, write each one as you find it
5. **Number files sequentially**: `001-category-title.md`, `002-category-title.md`, etc.
6. **Use jcodemunch MCP** for all code analysis — not raw grep/read
7. **Use mysql MCP** (read-only) for all DB analysis
8. **After context compaction**: Read `debug_output/.loop_state` FIRST to recover your mission, current phase, and iteration
9. **Update `.loop_state`** after every phase completion
10. **Use `register_edit`** after writing any files to keep the jcodemunch index fresh

## CONTEXT COMPACTION RECOVERY

If you suspect context was compacted (you don't remember starting this task):
1. Read `debug_output/.loop_state` — it contains everything you need
2. Continue from the phase marked as current
3. Do NOT restart from Phase 1 unless the loop state says iteration should increment

## SEVERITY GUIDE
- **critical**: RCE, data exposure, auth bypass, SQL injection, data loss
- **high**: XSS, race conditions with data corruption, hardcoded production secrets
- **medium**: Dead code, circular deps, missing error handling, missing indexes
- **low**: Code smells, style issues, missing types, redundant indexes

## WHAT TO DO RIGHT NOW

Start executing from Phase 1 (RECON). Do not ask the user anything. Go.
