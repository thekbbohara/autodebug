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

### Improved Detection Rules
The severity guide and pattern lists in the skill file are meant to evolve. If you find new patterns worth scanning for, add them.

### Tooling Improvements
- `scripts/runner.py` — task persistence and state tracking
- `scripts/repo_audit.py` — structured finding management

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

This verifies the skill file parses correctly and all referenced tools exist.

## PR Process

1. Ensure the test script passes
2. Keep PRs focused — one feature per PR
3. Include a clear description of what changed and why
4. If adding a new scan phase, document which focus modes include it
