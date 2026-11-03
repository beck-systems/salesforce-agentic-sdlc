#!/usr/bin/env python3
"""PreToolUse guard for read-only /sf-ticket agents (sf-intake, sf-org-investigator,
sf-repo-investigator, sf-verifier). Bash: blocks anything that changes an org, git, or a
protected path. Write/Edit: only the cases dir and tmp, never approved.json."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_guard_lib import (ALLOW, CASES, DEFER, bash_decision, classify_readonly,
                          classify_write_path, emit, read_input)

data = read_input()
tool, ti = data.get("tool_name", ""), data.get("tool_input", {}) or {}

if tool == "Bash":
    d, r = bash_decision(ti.get("command", ""), classify_readonly)
    # Read-only reads defer to normal permissions rather than auto-allowing.
    emit(DEFER if d == ALLOW else d, r)

if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    d, r = classify_write_path(ti.get("file_path") or ti.get("notebook_path"), [CASES])
    emit(DEFER if d == ALLOW else d, r)

emit(DEFER, "not guarded")
