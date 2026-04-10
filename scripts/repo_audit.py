#!/usr/bin/env python3
"""Structured repo audit with finding tracking and solution plan generation."""

import json
import sys
from datetime import datetime
from pathlib import Path

AUDITS_DIR = Path(__file__).parent / "audits"


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
            "10_solution_plan": {"status": "pending", "description": "Prioritized solution plan with effort estimates"},
        },
        "findings": [],
        "files_analyzed": [],
        "current_phase": None,
    }
    (d / "state.json").write_text(json.dumps(state, indent=2))
    (d / "findings.json").write_text(json.dumps({"findings": []}, indent=2))
    (d / "solution_plan.md").write_text("# Solution Plan\n\n_Generated after all phases complete_\n\n")
    print(f"Initialized audit '{audit_id}' for {repo_path}")
    return state


def load_state(audit_id):
    d = AUDITS_DIR / audit_id
    return json.loads((d / "state.json").read_text())


def save_state(audit_id, state):
    d = AUDITS_DIR / audit_id
    (d / "state.json").write_text(json.dumps(state, indent=2))


def add_finding(audit_id, category, severity, title, description, file_path=None, line=None, suggestion=None):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())
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


def get_findings(audit_id, category=None, severity=None):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())["findings"]
    if category:
        findings = [f for f in findings if f["category"] == category]
    if severity:
        findings = [f for f in findings if f["severity"] == severity]
    return findings


def generate_solution_plan(audit_id):
    d = AUDITS_DIR / audit_id
    findings = json.loads((d / "findings.json").read_text())["findings"]

    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: sev_order.get(f["severity"], 5))

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
    state["phases"]["10_solution_plan"]["status"] = "completed"
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
        findings = get_findings(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        for f in findings:
            print(f"  [{f['severity'].upper()}] {f['id']}: {f['title']} ({f.get('file_path', '-')})")
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
