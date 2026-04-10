# Contributing to AutoDebug

## Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/autodebug.git`
3. Create a branch: `git checkout -b feature/my-feature`
4. Make your changes
5. Push: `git push origin feature/my-feature`
6. Open a Pull Request

## What You Can Contribute

### New Scan Phases
Add a new phase to `skills/autodebug.md` following the existing format. Each phase should:
- Have a clear number and name
- Specify which jcodemunch/mysql tools it uses
- Define what patterns it looks for
- State which focus modes include it
- Be added to `scripts/repo_audit.py` `init_audit` phases dict
- Be added to `scripts/test_skill.py` `test_required_sections`

### Improved Detection Rules
The severity guide and pattern lists in the skill file are meant to evolve. If you find new patterns worth scanning for, add them.

### Tooling Improvements
- `scripts/runner.py` — task persistence and state tracking
- `scripts/repo_audit.py` — structured finding management with dedup, ignore list, snapshots, and diffing

### Documentation
- New guides in `docs/`
- Better examples
- Translations

## Style Guide

- No comments or docstrings unless logic is genuinely non-obvious
- Follow existing code patterns in the repo
- Keep the skill prompt concise — it gets injected into the AI's context window

## Testing

Run the validation script:
```bash
python3 scripts/test_skill.py
```

This validates:
- Skill file parses correctly with all 6 arguments
- All 23 required sections present (13 phases + Issue/Solution + compaction recovery + testrules + dedup + ignore + severity + notifications + incremental + parallel)
- Testrules file parses correctly with all 8 steps
- repo_audit.py has all 13 phases
- repo_audit.py deduplication works
- repo_audit.py ignore list works
- repo_audit.py snapshot and diff work
- repo_audit.py min-severity filter works
- Focus mode phase map is complete

## PR Process

1. Ensure the test script passes
2. Keep PRs focused — one feature per PR
3. Include a clear description of what changed and why
4. If adding a new scan phase, document which focus modes include it
5. If adding new arguments, update `test_skill.py` to verify them
