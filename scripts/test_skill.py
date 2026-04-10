#!/usr/bin/env python3
"""Validate that the autodebug skill files parse correctly."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILL_FILE = REPO_ROOT / "skills" / "autodebug.md"
TESTRULES_FILE = REPO_ROOT / "skills" / "testrules.md"


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
    assert "write_testcase" in fields.get("arguments", ""), "Missing write_testcase argument"
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
        "Phase 11: WRITE TEST CASES",
        "## Issue",
        "## Solution",
        "CONTEXT COMPACTION RECOVERY",
        "testrules.md",
    ]
    for section in required:
        assert section in text, f"Missing required section: {section}"
    print(f"PASS: All {len(required)} required sections present")


def test_testrules_file_exists():
    assert TESTRULES_FILE.exists(), f"Testrules file not found: {TESTRULES_FILE}"
    print("PASS: Testrules file exists")


def test_testrules_file_parses():
    text = TESTRULES_FILE.read_text()
    assert text.startswith("---"), "Testrules file must start with --- frontmatter"
    parts = text.split("---", 2)
    assert len(parts) >= 3, "Testrules file must have frontmatter and body"

    frontmatter = parts[1].strip()
    fields = {}
    for line in frontmatter.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        fields[key.strip().lower()] = val.strip()

    assert fields.get("name") == "testrules", f"Expected name=testrules, got {fields.get('name')}"
    print(f"PASS: Testrules file parses correctly (name={fields['name']})")


def test_testrules_required_sections():
    text = TESTRULES_FILE.read_text()
    required = [
        "STEP 0: DISCOVER EXISTING TEST PATTERNS",
        "STEP 1: PRODUCTION-GRADE TEST PRINCIPLES",
        "STEP 2: TEST GENERATION PER FINDING CATEGORY",
        "STEP 3: TEST FILE ORGANIZATION",
        "STEP 4: MOCKING STRATEGY",
        "STEP 5: ASSERTION QUALITY",
        "STEP 6: LANGUAGE-SPECIFIC PRODUCTION PATTERNS",
        "STEP 7: QUALITY CHECKLIST",
    ]
    for section in required:
        assert section in text, f"Missing required section in testrules: {section}"
    print(f"PASS: All {len(required)} testrules sections present")


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
        test_testrules_file_exists,
        test_testrules_file_parses,
        test_testrules_required_sections,
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
