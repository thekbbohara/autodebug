---
name: autodebug
description: Autonomous never-stop debugging loop — scans entire repo for bugs, security issues, performance problems, slow DB queries, Docker/API vulnerabilities. Writes findings to debug_output/*.md. Loops forever until manually killed.
triggers: ["/autodebug"]
tools: [mcp__jcodemunch__index_folder, mcp__jcodemunch__resolve_repo, mcp__jcodemunch__get_repo_health, mcp__jcodemunch__get_repo_outline, mcp__jcodemunch__suggest_queries, mcp__jcodemunch__find_dead_code, mcp__jcodemunch__get_dead_code_v2, mcp__jcodemunch__get_hotspots, mcp__jcodemunch__get_dependency_cycles, mcp__jcodemunch__get_layer_violations, mcp__jcodemunch__get_coupling_metrics, mcp__jcodemunch__search_text, mcp__jcodemunch__search_symbols, mcp__jcodemunch__get_file_outline, mcp__jcodemunch__get_symbol_source, mcp__jcodemunch__get_symbol_complexity, mcp__jcodemunch__get_call_hierarchy, mcp__jcodemunch__get_blast_radius, mcp__jcodemunch__get_class_hierarchy, mcp__jcodemunch__get_file_content, mcp__jcodemunch__find_importers, mcp__jcodemunch__find_references, mcp__jcodemunch__check_references, mcp__jcodemunch__get_context_bundle, mcp__jcodemunch__plan_turn, mcp__jcodemunch__register_edit, mcp__mysql__mysql_query, Read, Write, Edit, Bash, Glob, Grep, GetDiagnostics, SleepTimer, TaskCreate, TaskUpdate, TaskList, Skill]
when-to-use: Use when user says "/autodebug", "autodebug", "run autodebug", "debug entire repo", "find all bugs". User can optionally specify focus areas as arguments.
argument-hint: [focus: security|performance|db|dead-code|all] [scope: path-or-all] [write-testcase] [min-severity: critical|high|medium|low] [webhook: url] [parallel]
arguments: [focus, scope, write_testcase, min_severity, webhook_url, parallel]
context: inline
---

You are now in **AUTODEBUG MODE** — an autonomous, never-stop debugging loop.

## MISSION
Scan the current repo (or $SCOPE) continuously for bugs, security issues, performance problems, and slow DB queries. Write EVERY finding to `debug_output/*.md` using the exact format below. NEVER pause, NEVER ask for confirmation, NEVER stop until the user manually kills you.

## ARGUMENTS
- $FOCUS — What to focus on: `security`, `performance`, `db`, `dead-code`, or `all` (default: `all`)
- $SCOPE — Path to scan (default: current working directory)
- $WRITE_TESTCASE — If `write-testcase` is passed, generate production-grade test cases for every finding. Read `testrules.md` for full test writing rules.
- $MIN_SEVERITY — Minimum severity to report: `critical`, `high`, `medium`, or `low` (default: `low`). Findings below this threshold are skipped.
- $WEBHOOK_URL — If a webhook URL is passed, POST critical/high findings as JSON to this URL.
- $PARALLEL — If `parallel` is passed, run independent scan phases as sub-agents concurrently.

## SETUP (do this FIRST — always)

1. Determine the repo path: use `$SCOPE` if provided, otherwise use the current working directory.
2. Check if repo is indexed via jcodemunch: `resolve_repo { "path": "<repo_path>" }`
   - If not indexed: `index_folder { "path": "<repo_path>", "use_ai_summaries": false }`
   - On subsequent iterations (iteration > 1): `index_folder { "path": "<repo_path>", "use_ai_summaries": false, "incremental": true }`
3. Create `debug_output/` directory inside the repo if it doesn't exist.
4. Write a `.loop_state` file to `debug_output/.loop_state` containing:
   - Mission description, repo path, jcodemunch ID
   - Current phase and iteration number
   - Audit ID (generated: `autodebug-<timestamp>`)
   - `findings_index`: object mapping `{file_stem: severity}` for all findings written so far — used for dedup
   - Files scanned so far
   - This file is your SOURCE OF TRUTH after context compaction
5. Initialize audit tracking:
   - `Bash`: `python3 scripts/repo_audit.py init <audit_id> <repo_path>`
   - `Bash`: `python3 scripts/runner.py register <audit_id> "AutoDebug loop" 300`
6. Read `debug_output/.ignore_list.json` if it exists — these are won't-fix patterns to skip.
7. **If $WRITE_TESTCASE is passed**: Read `skills/testrules.md` (or `.cheetahclaws/skills/testrules.md`) in full. Before writing any test, complete Step 0 from testrules.md: discover the repo's existing test patterns.

## OUTPUT FORMAT (MANDATORY — every .md file MUST follow this)

```markdown
# [CATEGORY] Short Title

## Issue
- **File**: `path/to/file.py:LINE`
- **Severity**: critical | high | medium | low
- **Category**: security | bug | performance | dead-code | logic | type-safety | dependency | db | docker | api
- **Description**: What's wrong and why it matters

## Solution
- **Fix**: Exact code change or approach
- **Effort**: trivial | small | medium | large
- **Priority**: Must-fix | Should-fix | Nice-to-have
```

## DEDUPLICATION

Before writing ANY finding .md file:
1. Check `.loop_state` → `findings_index` for the file stem (e.g. `001-security-sql-injection`)
2. If the same `category + title + file_path + line` already exists in `findings_index`, SKIP it
3. When writing a new finding, add it to `findings_index` immediately
4. Use `repo_audit.py finding` to track findings — it auto-deduplicates by `category + title + file_path + line`

## IGNORE LIST

Users can mark findings as won't-fix by editing `debug_output/.ignore_list.json`:
```json
{"patterns": [{"category": "dead-code", "file_pattern": "src/legacy/*", "title_pattern": "unused"}]}
```
- Before writing any finding, check if it matches an ignore pattern (category, file glob, title regex)
- `repo_audit.py finding` auto-checks the ignore list
- Users manage ignore list manually or via `repo_audit.py ignore <audit_id> <category> <file_pattern> <title_pattern>`

## SEVERITY THRESHOLD

If `$MIN_SEVERITY` is set above `low`, skip findings below that threshold:
- `critical` → only critical findings
- `high` → critical + high
- `medium` → critical + high + medium
- `low` → everything (default)

## NOTIFICATIONS

If `$WEBHOOK_URL` is set:
- POST critical and high severity findings to the webhook immediately after writing
- Payload: `{"severity": "...", "category": "...", "title": "...", "file": "...", "description": "..."}`
- Use `Bash`: `curl -s -X POST -H 'Content-Type: application/json' -d '<json>' $WEBHOOK_URL`

## INCREMENTAL INDEXING

- On iteration 1: full `index_folder`
- On iteration 2+: use `index_folder` with `"incremental": true`
- After writing files during any phase: call `register_edit` with the modified file paths to keep the index fresh
- Store `"indexed": true` in `.loop_state` after first index so you know to use incremental on subsequent iterations

## PARALLEL MODE

If `$PARALLEL` is passed, spawn sub-agents for independent phases:
- **Agent A**: Phases 2 + 4 (dead-code + dependencies)
- **Agent B**: Phases 5 + 7 (security + type safety)
- **Agent C**: Phases 3 + 8 (hotspots + performance)
- **Agent D**: Phase 9 (DB scan)
- **Agent E**: Phase 11 (Docker scan)
- **Main agent**: Phase 1 (recon) + Phase 6 (logic — needs hotspot data) + Phase 10 (API contract) + Phase 12 (regression) + Phase 13 (test cases)
- After all sub-agents complete, merge findings into `.loop_state` findings_index
- Use `Agent` tool with `subagent_type="coder"` and `wait=false` for each group

## SCAN PHASES (execute in order, then loop back to Phase 1)

### Phase 1: RECON
- `get_repo_health` → overall stats, dead code %, hotspots
- `get_repo_outline` → structure, languages
- `suggest_queries` → hot areas to investigate
- Write `debug_output/000-recon.md` with repo health summary
- `Bash`: `python3 scripts/repo_audit.py phase <audit_id> 1_recon in_progress` (before) / `complete` (after)
- Mark phase complete in `.loop_state`

### Phase 2: DEAD CODE
- `find_dead_code` (granularity=symbol, min_confidence=0.5, include_tests=true)
- `get_dead_code_v2` (min_confidence=0.5)
- For each dead symbol: check findings_index for dedup, check ignore list, then write individual finding .md file
- `Bash`: `python3 scripts/repo_audit.py finding <audit_id> <category> <severity> <title> <desc> [file] [line] [suggestion]`
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

### Phase 10: API CONTRACT SCAN
- `search_text` for route definitions: `@route|@app\.route|router\.|app\.get|app\.post|app\.put|app\.delete|@GetMapping|@PostMapping|@RequestMapping|func.*Handler|def.*handler`
- `get_symbol_source` on route handler functions
- Check for: missing input validation on endpoints, missing auth decorators, no rate limiting
- Check for: inconsistent response shapes (some endpoints return `{data}`, others return raw), missing error response schemas
- Check for: endpoints accepting `Any` or untyped request bodies, missing content-type validation
- Write findings with `category: api`
- Skip if $FOCUS is `performance`, `dead-code`, or `db`

### Phase 11: DOCKER SCAN
- `search_text` for Dockerfile patterns: `FROM |COPY |ADD |RUN |EXPOSE |ENV |USER |HEALTHCHECK`
- `get_file_content` on Dockerfiles and docker-compose files
- Check for: running as root (`USER root` or no USER directive), no HEALTHCHECK, `ADD` instead of `COPY`
- Check for: `latest` tags, exposed privileged ports (< 1024), `chmod 777`, secrets in ENV
- Check for: no `.dockerignore`, multi-stage builds without cleanup, unnecessary packages
- Check docker-compose for: bind mounts to `/`, privileged mode, `network_mode: host`
- Write findings with `category: docker`
- Skip if $FOCUS is `performance`, `dead-code`, or `db`

### Phase 12: REGRESSION CHECK
- `Bash`: `python3 scripts/repo_audit.py snapshot <audit_id> <current_iteration>`
- If previous iteration snapshot exists: `Bash`: `python3 scripts/repo_audit.py diff <audit_id> <prev_iteration> <current_iteration>`
- Write `debug_output/NNN-iteration-diff.md` with new/resolved/changed findings
- Re-read source of previously scanned files, check for new issues
- `Bash`: `python3 scripts/runner.py update <audit_id>`
- Update `.loop_state` with iteration number and findings_index
- `Bash`: `python3 scripts/repo_audit.py phase <audit_id> 12_regression complete`
- Set SleepTimer for 300 seconds (5 minutes)
- When timer fires, START OVER from Phase 1

### Phase 13: WRITE TEST CASES (only if $WRITE_TESTCASE is passed)
- This phase runs AFTER all other phases complete each iteration
- **Read `skills/testrules.md`** — it contains the complete rules for writing production-grade tests
- Before writing ANY test, complete Step 0 from testrules.md:
  1. `get_file_tree` with `path_prefix="tests/"` or `path_prefix="__tests__/"` — discover test directory structure
  2. `get_file_outline` on 3-5 existing test files — extract framework, naming, structure
  3. `get_symbol_source` on representative test functions — understand mocking, assertions, fixtures
  4. Record the discovered patterns in `.loop_state` so you don't re-discover after compaction
- For EACH finding written in phases 2-11, write a companion test file:
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
| `all` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, [13 if write-testcase] |
| `security` | 1, 5, 7, 10, 11, 12, [13 if write-testcase] |
| `performance` | 1, 3, 8, 9, 12, [13 if write-testcase] |
| `db` | 1, 9, 12, [13 if write-testcase] |
| `dead-code` | 1, 2, 4, 12, [13 if write-testcase] |

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
11. **Dedup before writing** — check findings_index in `.loop_state` before writing any .md file
12. **Respect ignore list** — skip findings matching `debug_output/.ignore_list.json` patterns
13. **Respect severity threshold** — skip findings below `$MIN_SEVERITY`
14. **Notify on critical/high** — if `$WEBHOOK_URL` is set, POST critical and high findings immediately

## CONTEXT COMPACTION RECOVERY

If you suspect context was compacted (you don't remember starting this task):
1. Read `debug_output/.loop_state` — it contains everything you need
2. Continue from the phase marked as current
3. Do NOT restart from Phase 1 unless the loop state says iteration should increment
4. Re-read the audit ID from `.loop_state` for repo_audit.py commands

## SEVERITY GUIDE
- **critical**: RCE, data exposure, auth bypass, SQL injection, data loss
- **high**: XSS, race conditions with data corruption, hardcoded production secrets
- **medium**: Dead code, circular deps, missing error handling, missing indexes
- **low**: Code smells, style issues, missing types, redundant indexes

## WHAT TO DO RIGHT NOW

Start executing from Phase 1 (RECON). Do not ask the user anything. Go.
