#!/usr/bin/env python3
"""Validate that the autodebug skill file parses correctly."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILL_FILE = REPO_ROOT / "skills" / "autodebug.md"


def test_skill_file_exists():
    assert SKILL_FILE.exists(), f"Skill file not found: {SKILL_FILE}"
    print("PASS: Skill file exists")


def test_skill_file_parses():
    text = SKILL_FILE.read_text()
    assert text.startswith("---"), "Skill file must start with --- frontmatter"
    parts = text.split("---", 2)
    assert len(parts) >= 3, "Skill file must have frontmatter and body"

    frontmatter = parts[1].strip()
    fields = {}
    for line in frontmatter.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fields[key.strip().lower()] = val.strip()

    assert fields.get("name") == "autodebug", f"Expected name=autodebug, got {fields.get('name')}"
    assert "/autodebug" in fields.get("triggers", ""), "Missing /autodebug trigger"
    print(f"PASS: Skill file parses correctly (name={fields['name']})")


def test_required_sections():
    text = SKILL_FILE.read_text()
    required = [
        "Phase 1: RECON",
        "Phase 2: DEAD CODE",
        "Phase 3: HOTSPOTS",
        "Phase 4: DEPENDENCIES",
        "Phase 5: SECURITY",
        "Phase 6: LOGIC BUGS",
        "Phase 7: TYPE SAFETY",
        "Phase 8: PERFORMANCE",
        "Phase 9: DB SCAN",
        "Phase 10: REGRESSION",
        "## Issue",
        "## Solution",
        "CONTEXT COMPACTION RECOVERY",
    ]
    for section in required:
        assert section in text, f"Missing required section: {section}"
    print(f"PASS: All {len(required)} required sections present")


def test_scripts_exist():
    scripts = REPO_ROOT / "scripts"
    assert (scripts / "runner.py").exists(), "Missing scripts/runner.py"
    assert (scripts / "repo_audit.py").exists(), "Missing scripts/repo_audit.py"
    print("PASS: All scripts exist")


def main():
    tests = [
        test_skill_file_exists,
        test_skill_file_parses,
        test_required_sections,
        test_scripts_exist,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1

    if failed:
        print(f"\n{failed} test(s) failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed!")


if __name__ == "__main__":
    main()
