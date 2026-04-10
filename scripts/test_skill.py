#!/usr/bin/env python3
"""Validate that the autodebug skill files parse correctly and repo_audit.py works."""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILL_FILE = REPO_ROOT / "skills" / "autodebug.md"
TESTRULES_FILE = REPO_ROOT / "skills" / "testrules.md"
REPO_AUDIT = REPO_ROOT / "scripts" / "repo_audit.py"


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
    assert "min_severity" in fields.get("arguments", ""), "Missing min_severity argument"
    assert "webhook_url" in fields.get("arguments", ""), "Missing webhook_url argument"
    assert "parallel" in fields.get("arguments", ""), "Missing parallel argument"
    print(f"PASS: Skill file parses correctly (name={fields['name']})")


def test_required_sections():
    text = SKILL_FILE.read_text()
    required = [
        "Phase 1: RECON",
        "Phase 2: DEAD CODE",
        "Phase 3: HOTSPOTS",
        "Phase 4: DEPENDENCIES",
        "Phase 5: SECURITY SCAN",
        "Phase 6: LOGIC BUGS",
        "Phase 7: TYPE SAFETY",
        "Phase 8: PERFORMANCE",
        "Phase 9: DB SCAN",
        "Phase 10: API CONTRACT SCAN",
        "Phase 11: DOCKER SCAN",
        "Phase 12: REGRESSION CHECK",
        "Phase 13: WRITE TEST CASES",
        "## Issue",
        "## Solution",
        "CONTEXT COMPACTION RECOVERY",
        "testrules.md",
        "## DEDUPLICATION",
        "## IGNORE LIST",
        "## SEVERITY THRESHOLD",
        "## NOTIFICATIONS",
        "## INCREMENTAL INDEXING",
        "## PARALLEL MODE",
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


def test_repo_audit_has_13_phases():
    import importlib.util
    spec = importlib.util.spec_from_file_location("repo_audit", REPO_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmpdir = tempfile.mkdtemp()
    try:
        orig_audits_dir = mod.AUDITS_DIR
        mod.AUDITS_DIR = Path(tmpdir)
        state = mod.init_audit("test-13-phases", "/tmp/test")

        expected_phases = [
            "1_recon", "2_dead_code", "3_hotspots", "4_dependency_issues",
            "5_security_scan", "6_logic_bugs", "7_type_safety", "8_performance",
            "9_db_scan", "10_api_contract", "11_docker_scan", "12_regression",
            "13_write_test_cases",
        ]
        for phase in expected_phases:
            assert phase in state["phases"], f"Missing phase: {phase}"
        assert len(state["phases"]) == 13, f"Expected 13 phases, got {len(state['phases'])}"
        print("PASS: repo_audit.py has 13 phases")
    finally:
        shutil.rmtree(tmpdir)


def test_repo_audit_dedup():
    import importlib.util
    spec = importlib.util.spec_from_file_location("repo_audit", REPO_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmpdir = tempfile.mkdtemp()
    try:
        mod.AUDITS_DIR = Path(tmpdir)
        mod.init_audit("test-dedup", "/tmp/test")

        fid1 = mod.add_finding("test-dedup", "security", "high", "SQL Injection", "desc", "src/db.py", "42", "Use parameterized queries")
        assert fid1 is not None, "First finding should be added"

        fid2 = mod.add_finding("test-dedup", "security", "high", "SQL Injection", "desc", "src/db.py", "42", "Use parameterized queries")
        assert fid2 is None, "Duplicate finding should be skipped"

        fid3 = mod.add_finding("test-dedup", "security", "high", "SQL Injection", "desc", "src/db.py", "99", "Fix")
        assert fid3 is not None, "Same title but different line should be different"

        fid4 = mod.add_finding("test-dedup", "security", "high", "XSS", "desc", "src/db.py", "42", "Fix")
        assert fid4 is not None, "Different title at same location should be different"
        print("PASS: repo_audit.py deduplication works")
    finally:
        shutil.rmtree(tmpdir)


def test_repo_audit_ignore():
    import importlib.util
    spec = importlib.util.spec_from_file_location("repo_audit", REPO_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmpdir = tempfile.mkdtemp()
    try:
        mod.AUDITS_DIR = Path(tmpdir)
        mod.init_audit("test-ignore", "/tmp/test")

        mod.add_ignore("test-ignore", "dead-code", "", "")
        fid1 = mod.add_finding("test-ignore", "dead-code", "low", "Unused function", "desc", "src/old.py")
        assert fid1 is None, "Ignored category finding should be skipped"

        fid2 = mod.add_finding("test-ignore", "security", "high", "XSS", "desc", "src/app.py")
        assert fid2 is not None, "Non-ignored category finding should be added"

        patterns = mod.load_ignore_list("test-ignore")
        assert len(patterns) == 1, "Should have 1 ignore pattern"

        mod.remove_ignore("test-ignore", 0)
        patterns = mod.load_ignore_list("test-ignore")
        assert len(patterns) == 0, "Should have 0 ignore patterns after removal"
        print("PASS: repo_audit.py ignore list works")
    finally:
        shutil.rmtree(tmpdir)


def test_repo_audit_snapshot_diff():
    import importlib.util
    spec = importlib.util.spec_from_file_location("repo_audit", REPO_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmpdir = tempfile.mkdtemp()
    try:
        mod.AUDITS_DIR = Path(tmpdir)
        mod.init_audit("test-snap", "/tmp/test")

        mod.add_finding("test-snap", "security", "high", "Bug A", "desc", "src/a.py")
        mod.add_finding("test-snap", "bug", "medium", "Bug B", "desc", "src/b.py")
        snap1 = mod.snapshot_audit("test-snap", 1)
        assert snap1["iteration"] == 1
        assert len(snap1["findings"]) == 2

        mod.add_finding("test-snap", "security", "critical", "Bug C", "desc", "src/c.py")
        snap2 = mod.snapshot_audit("test-snap", 2)
        assert len(snap2["findings"]) == 3

        diff = mod.diff_audits("test-snap", 1, 2)
        assert len(diff["new"]) == 1, f"Expected 1 new finding, got {len(diff['new'])}"
        assert diff["new"][0]["title"] == "Bug C"
        assert len(diff["resolved"]) == 0
        print("PASS: repo_audit.py snapshot and diff work")
    finally:
        shutil.rmtree(tmpdir)


def test_repo_audit_min_severity():
    import importlib.util
    spec = importlib.util.spec_from_file_location("repo_audit", REPO_AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tmpdir = tempfile.mkdtemp()
    try:
        mod.AUDITS_DIR = Path(tmpdir)
        mod.init_audit("test-sev", "/tmp/test")

        mod.add_finding("test-sev", "security", "critical", "RCE", "desc", "src/a.py")
        mod.add_finding("test-sev", "security", "high", "XSS", "desc", "src/b.py")
        mod.add_finding("test-sev", "bug", "medium", "Null check", "desc", "src/c.py")
        mod.add_finding("test-sev", "style", "low", "Typo", "desc", "src/d.py")

        all_findings = mod.get_findings("test-sev")
        assert len(all_findings) == 4

        high_only = mod.get_findings("test-sev", min_severity="high")
        assert len(high_only) == 2, f"Expected 2 findings (critical+high), got {len(high_only)}"

        critical_only = mod.get_findings("test-sev", min_severity="critical")
        assert len(critical_only) == 1, f"Expected 1 finding (critical), got {len(critical_only)}"
        print("PASS: repo_audit.py min-severity filter works")
    finally:
        shutil.rmtree(tmpdir)


def test_focus_mode_phase_map():
    text = SKILL_FILE.read_text()
    focus_modes = ["all", "security", "performance", "db", "dead-code"]
    for mode in focus_modes:
        assert mode in text, f"Missing focus mode in phase map: {mode}"
    assert "Phase 10: API CONTRACT SCAN" in text, "API contract phase missing from focus map"
    assert "Phase 11: DOCKER SCAN" in text, "Docker phase missing from focus map"
    assert "Phase 12: REGRESSION CHECK" in text, "Regression phase wrong number"
    assert "Phase 13: WRITE TEST CASES" in text, "Test cases phase wrong number"
    print("PASS: Focus mode phase map includes all modes and phases 10-13")


def main():
    tests = [
        test_skill_file_exists,
        test_skill_file_parses,
        test_required_sections,
        test_testrules_file_exists,
        test_testrules_file_parses,
        test_testrules_required_sections,
        test_scripts_exist,
        test_repo_audit_has_13_phases,
        test_repo_audit_dedup,
        test_repo_audit_ignore,
        test_repo_audit_snapshot_diff,
        test_repo_audit_min_severity,
        test_focus_mode_phase_map,
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
