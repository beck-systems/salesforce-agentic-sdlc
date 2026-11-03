#!/usr/bin/env python3
"""PreToolUse guard for sf-qa.

QA creates and updates test records, so it can write data, but never metadata:
- build org: sf data writes and Apex test runs ALLOWED.
- qa org: sf data writes ASK; Apex test runs ALLOWED.
- Prod (or any unrecognised org): DENY. Missing -o: DENY.
- No deploys, no anonymous Apex, no git writes.
- Write/Edit: the cases dir and tmp only.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_guard_lib import (ALLOW, ASK, CASES, DEFER, DENY, bash_decision, classify_readonly,
                          classify_write_path, emit, org_kind, read_input, target_org)

data = read_input()
tool, ti = data.get("tool_name", ""), data.get("tool_input", {}) or {}


def data_write(seg, what):
    kind = org_kind(target_org(seg))
    if kind is None:
        return DENY, f"{what}: pass an explicit -o <build|qa org>"
    if kind == "prod":
        return DENY, f"{what}: QA never writes to Prod (orchestrator verifies Prod)"
    if kind == "qa":
        return ASK, f"{what} on the QA org needs the operator's confirmation"
    return ALLOW, f"{what} on the build org"


def classify_qa(seg):
    s = seg
    if re.search(r"\bsf\s+apex\s+run\s+test\b", s):
        kind = org_kind(target_org(s))
        return (ALLOW, "apex tests") if kind in ("build", "qa") else (DENY, "apex tests: build/qa orgs only")
    if re.search(r"\bsf\s+data\s+(create|update|upsert)\b", s):
        return data_write(s, "test-record write")
    if re.search(r"\bsf\s+data\s+(delete|import|bulk)\b", s):
        return DENY, "deletes and bulk loads go to the operator"
    if re.search(r"\bsf\s+api\s+request\s+rest", s):
        m = re.search(r"(?:-X|--method)(?:\s+|=)['\"]?(\w+)", s)
        if (m and m.group(1).upper() in ("POST", "PATCH")) and "/sobjects/" in s:
            return data_write(s, "REST record write")
    return classify_readonly(s)


if tool == "Bash":
    d, r = bash_decision(ti.get("command", ""), classify_qa)
    emit(d, r)

if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    d, r = classify_write_path(ti.get("file_path") or ti.get("notebook_path"), [CASES])
    emit(DEFER if d == ALLOW else d, r)

emit(DEFER, "not guarded")
