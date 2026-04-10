#!/usr/bin/env python3
"""Autonomous task persistence — survives AI context compaction."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

AUTONOMOUS_DIR = Path(__file__).parent
TASKS_FILE = AUTONOMOUS_DIR / "active_tasks.json"
LOG_FILE = AUTONOMOUS_DIR / "loop.log"


def load_tasks():
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return {"tasks": {}}


def save_tasks(data):
    TASKS_FILE.write_text(json.dumps(data, indent=2))


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    LOG_FILE.exists() or LOG_FILE.touch()
    with open(LOG_FILE, "a") as f:
        f.write(line)
    print(line, end="")


def register_task(task_id, description, interval_seconds, command=None, max_iterations=None):
    tasks = load_tasks()
    tasks["tasks"][task_id] = {
        "description": description,
        "interval_seconds": interval_seconds,
        "command": command,
        "max_iterations": max_iterations,
        "current_iteration": 0,
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "next_run": datetime.now().isoformat(),
    }
    save_tasks(tasks)
    log(f"Registered task '{task_id}': {description}")


def update_iteration(task_id):
    tasks = load_tasks()
    if task_id not in tasks["tasks"]:
        log(f"ERROR: Task '{task_id}' not found")
        return False
    task = tasks["tasks"][task_id]
    task["current_iteration"] += 1
    task["last_run"] = datetime.now().isoformat()
    if task["max_iterations"] and task["current_iteration"] >= task["max_iterations"]:
        task["status"] = "completed"
    else:
        task["next_run"] = datetime.now().isoformat()
    save_tasks(tasks)
    log(f"Task '{task_id}' iteration {task['current_iteration']}/{task['max_iterations'] or 'inf'} - {task['status']}")
    return task["status"] == "active"


def pause_task(task_id):
    tasks = load_tasks()
    if task_id in tasks["tasks"]:
        tasks["tasks"][task_id]["status"] = "paused"
        save_tasks(tasks)
        log(f"Paused task '{task_id}'")


def resume_task(task_id):
    tasks = load_tasks()
    if task_id in tasks["tasks"]:
        tasks["tasks"][task_id]["status"] = "active"
        save_tasks(tasks)
        log(f"Resumed task '{task_id}'")


def stop_task(task_id):
    tasks = load_tasks()
    if task_id in tasks["tasks"]:
        tasks["tasks"][task_id]["status"] = "stopped"
        save_tasks(tasks)
        log(f"Stopped task '{task_id}'")


def get_active_tasks():
    tasks = load_tasks()
    return {k: v for k, v in tasks["tasks"].items() if v["status"] == "active"}


def get_task(task_id):
    tasks = load_tasks()
    return tasks["tasks"].get(task_id)


def list_tasks():
    tasks = load_tasks()
    for tid, t in tasks["tasks"].items():
        print(f"  {tid}: {t['description']} [{t['status']}] iter={t['current_iteration']}/{t['max_iterations'] or 'inf'} last={t['last_run'] or 'never'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        list_tasks()
    elif cmd == "register":
        register_task(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    elif cmd == "update":
        update_iteration(sys.argv[2])
    elif cmd == "pause":
        pause_task(sys.argv[2])
    elif cmd == "resume":
        resume_task(sys.argv[2])
    elif cmd == "stop":
        stop_task(sys.argv[2])
    elif cmd == "active":
        active = get_active_tasks()
        for tid, t in active.items():
            print(f"  {tid}: {t['description']} iter={t['current_iteration']}")
    elif cmd == "get":
        t = get_task(sys.argv[2])
        if t:
            print(json.dumps(t, indent=2))
