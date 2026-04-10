---
name: autodebug
description: Autonomous never-stop debugging loop — scans entire repo for bugs, security issues, performance problems, slow DB queries, Docker/API vulnerabilities. Writes findings to debug_output/*.md. Loops forever until manually killed.
triggers: ["/autodebug"]
tools: [mcp__jcodemunch__index_folder, mcp__jcodemunch__resolve_repo, mcp__jcodemunch__get_repo_health, mcp__jcodemunch__get_repo_outline, mcp__jcodemunch__suggest_queries, mcp__jcodemunch__find_dead_code, mcp__jcodemunch__get_dead_code_v2, mcp__jcodemunch__get_hotspots, mcp__jcodemunch__get_dependency_cycles, mcp__jcodemunch__get_layer_violations, mcp__jcodemunch__get_coupling_metrics, mcp__jcodemunch__search_text, mcp__jcodemunch__search_symbols, mcp__jcodemunch__get_file_outline, mcp__jcodemunch__get_symbol_source, mcp__jcodemunch__get_symbol_complexity, mcp__jcodemunch__get_call_hierarchy, mcp__jcodemunch__get_blast_radius, mcp__jcodemunch__get_class_hierarchy, mcp__jcodemunch__get_file_content, mcp__jcodemunch__find_importers, mcp__jcodemunch__find_references, mcp__jcodemunch__check_references, mcp__jcodemunch__get_context_bundle, mcp__jcodemunch__plan_turn, mcp__jcodemunch__register_edit, mcp__mysql__mysql_query, Read, Write, Edit, Bash, Glob, Grep, GetDiagnostics, SleepTimer, TaskCreate, TaskUpdate, TaskList, Skill]
when-to-use: Use when user says "/autodebug", "autodebug", "run autodebug", "debug entire repo", "find all bugs". User can optionally specify focus areas as arguments.
argument-hint: [focus: security|performance|db|dead-code|all] [scope: path-or-all] [target: file|dir|class|function] [discover-logic] [write-testcase] [min-severity: critical|high|medium|low] [webhook: url] [parallel]
arguments: [focus, scope, target, discover_logic, write_testcase, min_severity, webhook_url, parallel]
context: inline
---

You are now in **AUTODEBUG MODE** — an autonomous, never-stop debugging loop.

## MISSION
Scan the current repo (or $SCOPE) continuously for bugs, security issues, performance problems, and slow DB queries. Write EVERY finding to `debug_output/*.md` using the exact format below. NEVER stop until the user manually kills you.

**EXCEPTION — Phase 0 (Business Logic Discovery)**: Only runs when `discover-logic` is passed. This is the ONLY phase where you MUST pause and ask the user for confirmation. You cannot find logic bugs without understanding the correct business logic. Present your inference, ask questions about things you're unsure about, and get explicit confirmation before proceeding to Phase 1.

## ARGUMENTS
- $FOCUS — What to focus on: `security`, `performance`, `db`, `dead-code`, or `all` (default: `all`)
- $SCOPE — Repo root path (default: current working directory)
- $TARGET — Specific target to debug. Can be a file path (`src/models/user.py`), directory (`src/services/`), class name (`UserService`), or function name (`calculatePrice`). When set, all scan phases are scoped to this target and its direct dependents only. Default: entire repo.
- $DISCOVER_LOGIC — If `discover-logic` is passed, run Phase 0 (Business Logic Discovery) before scanning. The agent will infer business rules from the code, present them to you, ask questions, and only proceed after your confirmation. This makes Phase 6 (Logic Bugs) far more effective — it can find semantic bugs instead of just mechanical ones. Default: off.
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
7. **If $TARGET is set**: Resolve the target to a concrete set of files and symbols:
   - If $TARGET is a file path (e.g. `src/models/user.py`): resolve to that file, get its outline, mark as primary target
   - If $TARGET is a directory (e.g. `src/services/`): resolve to all source files in that directory
   - If $TARGET is a class name (e.g. `UserService`): `search_symbols` with `query="$TARGET"` and `kind="class"` to find it, then `get_symbol_source` + `get_class_hierarchy`
   - If $TARGET is a function name (e.g. `calculatePrice`): `search_symbols` with `query="$TARGET"` and `kind="function"` to find it
   - For class/function targets: also resolve their file via the search result, then get `get_call_hierarchy` (both directions) and `get_blast_radius` to find direct callers/callees
   - Write the resolved target scope to `.loop_state` → `target_scope` with: primary files, primary symbol IDs, related files (callers/callees/dependents), related symbol IDs
   - All subsequent phases will restrict their scanning to files in `target_scope`
8. **If $WRITE_TESTCASE is passed**: Read `skills/testrules.md` (or `.cheetahclaws/skills/testrules.md`) in full. Before writing any test, complete Step 0 from testrules.md: discover the repo's existing test patterns.

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

## BUSINESS LOGIC DISCOVERY

Before scanning for bugs, autodebug can discover what the code is *supposed* to do. This is Phase 0, enabled by passing `discover-logic`.

**Why**: Without confirmed business logic, Phase 6 can only find mechanical bugs (missing null checks, bare except, etc.). With confirmed business logic, Phase 6 can find *semantic* bugs — code that runs without crashing but produces wrong business outcomes.

**Process**:
1. Infer business logic from code signals (models, routes, services, naming, queries, config)
2. Write `debug_output/000-business-logic.md` with inferred rules, entities, workflows, calculations
3. Present summary + questions to user via `AskUserQuestion`
4. User confirms/corrects/answers questions
5. Update `000-business-logic.md` and write confirmed logic to `.loop_state` → `business_logic`
6. Only then proceed to Phase 1

**What counts as a business rule**:
- Validation rules: "email must be unique", "quantity must be > 0"
- State transitions: "order can go from pending → paid → shipped → delivered"
- Calculations: "tax = subtotal × rate", "discount applied before tax"
- Access control: "only admin can delete users", "users can only edit own posts"
- Data constraints: "one active subscription per user", "invoice number is sequential per year"
- Side effects: "cancellation triggers refund", "signup sends welcome email"

**How Phase 6 uses it**: Each confirmed rule is traced through code. If the implementation violates or misses a confirmed rule, that's a `category: logic` finding — a real business bug, not just a code smell.

**Iteration 2+**: Phase 0 is skipped — confirmed logic is already in `.loop_state`. If missing, re-run Phase 0.

## TARGET SCOPING

If `$TARGET` is set, all scan phases are restricted to the target and its direct dependents:

- **File target** (`src/models/user.py`): scan that file + files that import it
- **Directory target** (`src/services/`): scan all source files in that directory + their direct importers
- **Class target** (`UserService`): scan the class definition, its methods, its hierarchy (parent/subclasses), and its callers/callees
- **Function target** (`calculatePrice`): scan the function, its callees, and its callers

**How targeting affects each phase**:
- **Phase 0 (BUSINESS LOGIC)**: narrow inference to target's domain only
- **Phase 1 (RECON)**: still runs repo-wide but highlights the target's health metrics
- **Phase 2 (DEAD CODE)**: only checks if the target or its symbols are dead code
- **Phase 3 (HOTSPOTS)**: only checks complexity of target symbols
- **Phase 4 (DEPENDENCIES)**: only checks dependency cycles involving target files
- **Phase 5 (SECURITY)**: only scans target files + direct dependents for security patterns
- **Phase 6 (LOGIC BUGS)**: deep-read target source only
- **Phase 7 (TYPE SAFETY)**: `GetDiagnostics` on target files only
- **Phase 8 (PERFORMANCE)**: only scans target + callees for perf issues
- **Phase 9 (DB SCAN)**: runs normally (DB analysis is schema-wide, not file-scoped)
- **Phase 10 (API CONTRACT)**: only checks routes defined in target files
- **Phase 11 (DOCKER)**: runs normally (not file-scoped)

**In `.loop_state`**: `target_scope` stores `{primary_files, primary_symbols, related_files, related_symbols}` so it survives compaction.

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

### Phase 0: BUSINESS LOGIC DISCOVERY (only if `discover-logic` is passed)

This phase only runs when `$DISCOVER_LOGIC` is set. If not set, skip directly to Phase 1.

This phase is **mandatory when enabled** — you cannot find logic bugs if you don't know the correct business logic.

**Step 0.1: Infer business logic from code**

Analyze the codebase to infer what the business does, using these signals:

1. **Data models** → `search_symbols` with `kind="class"` in model directories (`models/`, `entities/`, `schemas/`). Read each model's fields via `get_symbol_source`. Infer: what entities exist, what relationships they have, what constraints are implied (e.g. `unique=True`, `nullable=False`).

2. **Routes/API endpoints** → `search_text` for route patterns (`@route`, `@app.route`, `router.`, `app.get`, `app.post`, etc.). For each endpoint, `get_symbol_source` on the handler. Infer: what actions the system supports, what inputs they take, what business rules they enforce.

3. **Service/business layer** → `search_symbols` in `services/`, `business/`, `handlers/`, `controllers/`. Read key functions. Infer: business rules, validation logic, state transitions, calculations.

4. **Database queries** → `search_text` for SQL patterns, ORM query patterns. Infer: what data relationships exist, what aggregates are computed, what filters are always applied.

5. **Configuration/consts** → `search_text` for `enum`, `const`, `config`, `setting`. Infer: business-defined thresholds, status codes, role definitions.

6. **Naming patterns** → Class names like `Order`, `Payment`, `Invoice`, `Subscription` reveal the domain. Function names like `calculateTax`, `applyDiscount`, `validateEligibility` reveal business rules.

**Step 0.2: Write Business Logic Summary**

Write `debug_output/000-business-logic.md` with this structure:

```markdown
# Business Logic Summary

## Domain
[What business/domain this codebase operates in — e.g. "E-commerce platform with multi-vendor marketplace"]

## Core Entities & Relationships
- **Entity1** → fields, constraints, relationships
- **Entity2** → fields, constraints, relationships
- [etc.]

## Business Rules (inferred from code)
1. **[RULE-01]**: [Description of inferred rule] — Source: `file.py:LINE` or `function_name`
2. **[RULE-02]**: [Description] — Source: ...
3. [etc.]

## State Machines / Workflows
- **[Workflow name]**: StateA → StateB → StateC (triggers, conditions)
- [etc.]

## Calculations & Formulas
- **[Formula name]**: `expression` — Source: `file.py:LINE`
- [etc.]

## Access Control Rules
- **[Role]**: can do [actions] — Source: middleware or decorator
- [etc.]

## Questions for User
1. ❓ [Thing you're unsure about — e.g. "Is the discount applied before or after tax?"]
2. ❓ [Ambiguous logic — e.g. "Can a user have multiple active subscriptions?"]
3. ❓ [Missing information — e.g. "What happens when payment fails after 3 retries?"]
4. [etc. — ask AS MANY questions as you have doubts about]
```

**Step 0.3: Present to user and ask for confirmation**

Use `AskUserQuestion` to present a condensed version:

```
I've analyzed the codebase and inferred the following business logic:

**Domain**: [one-liner]

**Key Business Rules** (summary of top 5-10):
- RULE-01: ...
- RULE-02: ...
- [etc.]

**Questions I have**:
1. ❓ ...
2. ❓ ...
3. ❓ ...

Please confirm or correct:
- Is the inferred logic correct?
- Any rules I missed?
- Any rules I got wrong?
- Answers to my questions?
```

**Step 0.4: Update with user's corrections**

After the user responds:
1. Update `debug_output/000-business-logic.md` with corrections and answers
2. Write the confirmed business logic to `.loop_state` → `business_logic` with structure:
   ```json
   {
     "domain": "...",
     "rules": [{"id": "RULE-01", "description": "...", "source": "file:line", "status": "confirmed|corrected|assumed"}],
     "questions_answered": [{"question": "...", "answer": "..."}],
     "confirmed_at": "ISO timestamp"
   }
   ```
3. Mark `0_business_logic` phase as `complete` in audit tracking

**If $TARGET is set**: Focus Phase 0 on the target's domain only. Still infer entity relationships, but narrow to entities/rules that interact with the target.

**This phase is SKIPPED on iteration 2+** — the confirmed business logic is already in `.loop_state`. Just verify it's still there and move to Phase 1. If `.loop_state` has no `business_logic` key (e.g. after manual deletion), re-run Phase 0.

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

### Phase 6: LOGIC BUGS (uses confirmed business logic from Phase 0 if available)
- If `business_logic` exists in `.loop_state` (Phase 0 was run):
  - **For each confirmed business rule** (RULE-01, RULE-02, etc.):
    - Trace the rule through the codebase using `get_symbol_source`, `find_references`, `get_call_hierarchy`
    - Check: does the code actually implement the rule correctly? Or does it violate it?
    - Common violations: wrong order of operations (e.g. discount applied after tax instead of before), missing state transition guards, skipped validation steps, race conditions on state changes
  - **For each question answered by user**: verify the code matches the user's answer. If not, that's a logic bug.
  - **Cross-reference rules**: if RULE-01 says "users can't cancel after shipping" but `cancelOrder()` doesn't check shipment status → that's a logic bug
  - Write each finding with `category: logic` when it's a business rule violation
- **Always check** for mechanical bugs: `.then(` without `.catch`, bare `except:`, missing `try/finally`, off-by-one in loops, missing null/None checks
- Write mechanical findings with `category: bug`
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
| `all` | [0 if discover-logic], 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, [13 if write-testcase] |
| `security` | [0 if discover-logic], 1, 5, 7, 10, 11, 12, [13 if write-testcase] |
| `performance` | [0 if discover-logic], 1, 3, 8, 9, 12, [13 if write-testcase] |
| `db` | [0 if discover-logic], 1, 9, 12, [13 if write-testcase] |
| `dead-code` | [0 if discover-logic], 1, 2, 4, 12, [13 if write-testcase] |

## CRITICAL RULES

1. **NEVER pause** — keep scanning, keep writing
2. **EXCEPTION: Phase 0** — when `discover-logic` is passed, you MUST pause and ask for business logic confirmation before proceeding
3. **NEVER ask for confirmation** — except in Phase 0 (see above)
4. **NEVER stop** — loop forever until killed
5. **Write findings IMMEDIATELY** — don't batch, write each one as you find it
6. **Number files sequentially**: `001-category-title.md`, `002-category-title.md`, etc.
7. **Use jcodemunch MCP** for all code analysis — not raw grep/read
8. **Use mysql MCP** (read-only) for all DB analysis
9. **After context compaction**: Read `debug_output/.loop_state` FIRST to recover your mission, current phase, and iteration
10. **Update `.loop_state`** after every phase completion
11. **Use `register_edit`** after writing any files to keep the jcodemunch index fresh
12. **Dedup before writing** — check findings_index in `.loop_state` before writing any .md file
13. **Respect ignore list** — skip findings matching `debug_output/.ignore_list.json` patterns
14. **Respect severity threshold** — skip findings below `$MIN_SEVERITY`
15. **Notify on critical/high** — if `$WEBHOOK_URL` is set, POST critical and high findings immediately

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

Start executing from Phase 0 (BUSINESS LOGIC DISCOVERY) if `discover-logic` was passed, otherwise start from Phase 1 (RECON). Go.
