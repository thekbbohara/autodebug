#!/usr/bin/env python3
"""Structured repo audit with finding tracking and solution plan generation."""

import json
import sys
from datetime import datetime
from pathlib import Path

AUDITS_DIR = Path(__file__).parent / "audits"
SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def ensure_audit_dir(audit_id):
    d = AUDITS_DIR / audit_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def init_audit(audit_id, repo_path, repo_name=""):
    d = ensure_audit_dir(audit_id)
    state = {
        "id": audit_id,
        "repo_path": repo_path,
        "repo_name": repo_name,
        "status": "in_progress",
        "created_at": datetime.now().isoformat(),
        "phases": {
            "1_recon": {"status": "pending", "description": "Repo overview, structure, health metrics"},
            "2_dead_code": {"status": "pending", "description": "Dead code and unreachable symbols"},
            "3_hotspots": {"status": "pending", "description": "Complex + frequently changed code (bug risk)"},
            "4_dependency_issues": {"status": "pending", "description": "Circular deps, layer violations, coupling"},
            "5_security_scan": {"status": "pending", "description": "SQL injection, XSS, hardcoded secrets, unsafe patterns"},
            "6_logic_bugs": {"status": "pending", "description": "Unhandled exceptions, race conditions, missing awaits"},
            "7_type_safety": {"status": "pending", "description": "Type errors, unsafe casts, missing null checks"},
            "8_performance": {"status": "pending", "description": "N+1 queries, memory leaks, sync blocking"},
            "9_db_scan": {"status": "pending", "description": "MySQL slow queries, missing indexes, oversized tables"},
            "10_api_contract": {"status": "pending", "description": "API route validation, missing auth, inconsistent responses"},
            "11_docker_scan": {"status": "pending", "description": "Docker security: root user, latest tags, exposed ports, secrets in ENV"},
            "12_regression": {"status": "pending", "description": "Re-scan, snapshot, diff, sleep, loop"},
            "13_write_test_cases": {"status": "pending", "description": "Generate production-grade regression tests for findings"},
        },
        "findings": [],
        "files_analyzed": [],
        "current_phase": None,
    }
    (d / "state.json").write_text(json.dumps(state, indent=2))
    (d / "findings.json").write_text(json.dumps({"findings": []}, indent=2))
    (d / "ignore_list.json").write_text(json.dumps({"patterns": []}, indent=2))
    (d / "solution_plan.md").write_text("# Solution Plan\n\n_Generated after all phases complete_\n\n")
    print(f"Initialized audit '{audit_id}' for {repo_path}")
    return state


def load_state(audit_id):
    d = AUDITS_DIR / audit_id
    return json.loads((d / "state.json").read_text())


def save_state(audit_id, state):
    d = AUDITS_DIR / audit_id
    (d / "state.json").write_text(json.dumps(state, indent=2))


def load_ignore_list(audit_id):
    d = AUDITS_DIR / audit_id
    p = d / "ignore_list.json"
    if p.exists():
        return json.loads(p.read_text())["patterns"]
    return []


def save_ignore_list(audit_id, patterns):
    d = AUDITS_DIR / audit_id
    (d / "ignore_list.json").write_text(json.dumps({"patterns": patterns}, indent=2))


def matches_ignore(ignore_patterns, category, title, file_path):
    import fnmatch
    for pat in ignore_patterns:
        if pat.get("category") and pat["category"] != category:
            continue
        if pat.get("file_pattern") and file_path:
            if not fnmatch.fnmatch(file_path, pat["file_pattern"]):
                continue
        if pat.get("title_pattern"):
            import re
            if not re.search(pat["title_pattern"], title, re.IGNORECASE):
                continue
        return True
    return False


def add_finding(audit_id, category, severity, title, description, file_path=None, line=None, suggestion=None):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())

    for f in findings["findings"]:
        if (f["category"] == category and f["title"] == title
                and f.get("file_path") == file_path and f.get("line") == line):
            print(f"  SKIP (duplicate): {title} ({file_path or 'general'})")
            return None

    ignore_patterns = load_ignore_list(audit_id)
    if matches_ignore(ignore_patterns, category, title, file_path):
        print(f"  SKIP (ignored): {title} ({file_path or 'general'})")
        return None

    finding = {
        "id": f"F-{len(findings['findings'])+1:03d}",
        "category": category,
        "severity": severity,
        "title": title,
        "description": description,
        "file_path": file_path,
        "line": line,
        "suggestion": suggestion,
        "status": "open",
        "created_at": datetime.now().isoformat(),
    }
    findings["findings"].append(finding)
    (d / "findings.json").write_text(json.dumps(findings, indent=2))

    state = load_state(audit_id)
    state["findings"].append({"id": finding["id"], "title": title, "severity": severity})
    save_state(audit_id, state)
    print(f"  [{severity.upper()}] {finding['id']}: {title} ({file_path or 'general'})")
    return finding["id"]


def mark_phase(audit_id, phase, status):
    state = load_state(audit_id)
    if phase in state["phases"]:
        state["phases"][phase]["status"] = status
        state["current_phase"] = phase if status == "in_progress" else None
        save_state(audit_id, state)
        print(f"Phase '{phase}' -> {status}")


def next_pending_phase(audit_id):
    state = load_state(audit_id)
    for phase_key, phase_val in state["phases"].items():
        if phase_val["status"] == "pending":
            return phase_key, phase_val
    return None, None


def get_findings(audit_id, category=None, severity=None, min_severity=None):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())["findings"]
    if category:
        findings = [f for f in findings if f["category"] == category]
    if severity:
        findings = [f for f in findings if f["severity"] == severity]
    if min_severity:
        threshold = SEV_ORDER.get(min_severity, 4)
        findings = [f for f in findings if SEV_ORDER.get(f["severity"], 5) <= threshold]
    return findings


def add_ignore(audit_id, category="", file_pattern="", title_pattern=""):
    patterns = load_ignore_list(audit_id)
    entry = {}
    if category:
        entry["category"] = category
    if file_pattern:
        entry["file_pattern"] = file_pattern
    if title_pattern:
        entry["title_pattern"] = title_pattern
    patterns.append(entry)
    save_ignore_list(audit_id, patterns)
    print(f"Added ignore pattern: {entry}")


def remove_ignore(audit_id, index):
    patterns = load_ignore_list(audit_id)
    if 0 <= index < len(patterns):
        removed = patterns.pop(index)
        save_ignore_list(audit_id, patterns)
        print(f"Removed ignore pattern #{index}: {removed}")
    else:
        print(f"Invalid index {index}, {len(patterns)} patterns exist")


def snapshot_audit(audit_id, iteration):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())["findings"]
    snap = {
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "findings": [{"id": f["id"], "title": f["title"], "severity": f["severity"],
                      "category": f["category"], "file_path": f.get("file_path"),
                      "status": f["status"]} for f in findings],
    }
    snap_file = d / f"iteration_{iteration}.json"
    snap_file.write_text(json.dumps(snap, indent=2))
    print(f"Snapshot saved: iteration_{iteration}.json ({len(snap['findings'])} findings)")
    return snap


def diff_audits(audit_id, iter_a, iter_b):
    d = AUDITS_DIR / audit_id
    snap_a = json.loads((d / f"iteration_{iter_a}.json").read_text())
    snap_b = json.loads((d / f"iteration_{iter_b}.json").read_text())

    ids_a = {f["id"] for f in snap_a["findings"]}
    ids_b = {f["id"] for f in snap_b["findings"]}

    new_ids = ids_b - ids_a
    resolved_ids = ids_a - ids_b
    common_ids = ids_a & ids_b

    findings_by_id_b = {f["id"]: f for f in snap_b["findings"]}
    findings_by_id_a = {f["id"]: f for f in snap_a["findings"]}

    changed = []
    for fid in common_ids:
        fa, fb = findings_by_id_a[fid], findings_by_id_b[fid]
        if fa["status"] != fb["status"] or fa["severity"] != fb["severity"]:
            changed.append({"id": fid, "before": fa, "after": fb})

    result = {
        "iteration_a": iter_a,
        "iteration_b": iter_b,
        "new": [findings_by_id_b[fid] for fid in new_ids],
        "resolved": [findings_by_id_a[fid] for fid in resolved_ids],
        "changed": changed,
    }
    print(f"Diff iteration_{iter_a} vs iteration_{iter_b}:")
    print(f"  New: {len(result['new'])}, Resolved: {len(result['resolved'])}, Changed: {len(result['changed'])}")
    return result


def generate_solution_plan(audit_id):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())["findings"]

    findings.sort(key=lambda f: SEV_ORDER.get(f["severity"], 5))

    lines = [
        f"# Solution Plan - Audit {audit_id}",
        "",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        f"_Total findings: {len(findings)}_",
        "",
    ]

    sev_counts = {}
    for f in findings:
        sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
    lines.append("## Summary")
    for sev in ["critical", "high", "medium", "low", "info"]:
        if sev in sev_counts:
            lines.append(f"- **{sev.upper()}**: {sev_counts[sev]}")
    lines.append("")

    current_sev = None
    for f in findings:
        if f["severity"] != current_sev:
            current_sev = f["severity"]
            lines.append(f"## {current_sev.upper()}")
            lines.append("")

        lines.append(f"### {f['id']}: {f['title']}")
        if f.get("file_path"):
            loc = f":{f['line']}" if f.get("line") else ""
            lines.append(f"- **File**: `{f['file_path']}{loc}`")
        lines.append(f"- **Category**: {f['category']}")
        lines.append(f"- **Description**: {f['description']}")
        if f.get("suggestion"):
            lines.append(f"- **Fix**: {f['suggestion']}")
        lines.append("")

    (d / "solution_plan.md").write_text("\n".join(lines))

    state = load_state(audit_id)
    state["status"] = "completed"
    state["phases"]["13_write_test_cases"]["status"] = "completed"
    save_state(audit_id, state)

    print(f"\nSolution plan written to {d / 'solution_plan.md'}")
    print(f"Total findings: {len(findings)}")
    for sev in ["critical", "high", "medium", "low", "info"]:
        if sev in sev_counts:
            print(f"  {sev.upper()}: {sev_counts[sev]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "init":
        init_audit(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "state":
        print(json.dumps(load_state(sys.argv[2]), indent=2))
    elif cmd == "phase":
        if sys.argv[3] == "next":
            phase, info = next_pending_phase(sys.argv[2])
            print(f"Next: {phase} - {info['description']}" if phase else "All phases complete!")
        else:
            mark_phase(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "finding":
        add_finding(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6],
                    sys.argv[7] if len(sys.argv) > 7 else None,
                    sys.argv[8] if len(sys.argv) > 8 else None,
                    sys.argv[9] if len(sys.argv) > 9 else None)
    elif cmd == "findings":
        min_sev = None
        args = sys.argv[2:]
        if "--min-severity" in args:
            idx = args.index("--min-severity")
            min_sev = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        findings = get_findings(args[0], args[1] if len(args) > 1 else None, min_severity=min_sev)
        for f in findings:
            print(f"  [{f['severity'].upper()}] {f['id']}: {f['title']} ({f.get('file_path', '-')})")
    elif cmd == "ignore":
        add_ignore(sys.argv[2],
                   sys.argv[3] if len(sys.argv) > 3 else "",
                   sys.argv[4] if len(sys.argv) > 4 else "",
                   sys.argv[5] if len(sys.argv) > 5 else "")
    elif cmd == "unignore":
        remove_ignore(sys.argv[2], int(sys.argv[3]))
    elif cmd == "snapshot":
        snapshot_audit(sys.argv[2], int(sys.argv[3]))
    elif cmd == "diff":
        diff_audits(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "plan":
        generate_solution_plan(sys.argv[2])
    elif cmd == "list":
        if AUDITS_DIR.exists():
            for d in sorted(AUDITS_DIR.iterdir()):
                if d.is_dir() and (d / "state.json").exists():
                    s = json.loads((d / "state.json").read_text())
                    print(f"  {d.name}: {s['status']} ({len(s.get('findings', []))} findings)")
        else:
            print("No audits yet")
    else:
        print("Commands: init, state, phase, finding, findings, ignore, unignore, snapshot, diff, plan, list")
