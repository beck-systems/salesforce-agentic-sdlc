#!/usr/bin/env python3
"""PreToolUse guard for sf-builder.

- build org: real deploys / data writes / anonymous Apex / non-GET REST are ALLOWED (no prompt)
  once the case's approved.json matches spec.md.
- qa org: dry-run/validate allowed; real writes ASK (and still need approval).
- Prod (or any unrecognised org): DENY. Missing -o: DENY.
- git: commits only inside a <repo>-<KEY> worktree; never push/merge/pull/reset --hard.
- Write/Edit: worktrees and the cases dir only; never protected paths or approved.json.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_guard_lib import (ALLOW, ASK, BRANCH, BUILD_ALIAS, CASES, DEFER, DENY, REPO, WORKTREE_RE,
                          approval_ok, bash_decision, classify_readonly, classify_write_path, emit,
                          org_kind, read_input, target_org, ticket_key)

data = read_input()
tool, ti, cwd = data.get("tool_name", ""), data.get("tool_input", {}) or {}, data.get("cwd", "")
REPO_NAME = os.path.basename(REPO)


def org_write(seg, what, dry=False):
    kind = org_kind(target_org(seg))
    if kind is None:
        return DENY, f"{what}: pass an explicit -o <build|qa org>"
    if kind == "prod":
        return DENY, f"{what}: the builder never touches Prod (orchestrator only, after the operator's OK)"
    if dry:
        return ALLOW, f"{what} dry-run on {kind}"
    ok, why = approval_ok(ticket_key(seg, cwd))
    if not ok:
        return DENY, f"{what}: {why}"
    if kind == "qa":
        return ASK, f"{what} on the QA org (approved spec) needs the operator's confirmation"
    return ALLOW, f"{what} on the build org (approved spec)"


def git_repo_path(seg):
    m = re.search(r"\bgit\s+-C\s+(\S+)", seg)
    return os.path.realpath(os.path.expanduser(m.group(1).strip("'\""))) if m else os.path.realpath(cwd or ".")


def classify_builder(seg):
    s = seg
    if re.search(r"\bsf\s+project\s+deploy\s+(report|preview|resume|cancel)\b", s):
        return ALLOW, "deploy status"
    if re.search(r"\bsf\s+project\s+deploy\s+(start|validate|quick)\b", s):
        dry = "--dry-run" in s or re.search(r"\bdeploy\s+validate\b", s) is not None
        return org_write(s, "deploy", dry)
    if re.search(r"\bsf\s+project\s+delete\b", s):
        return DENY, "destructive deploys go to the operator"
    if re.search(r"\bsf\s+project\s+retrieve\b", s):
        kind = org_kind(target_org(s))
        return (ALLOW, "retrieve") if kind else (DENY, "retrieve: pass an explicit -o")
    if re.search(r"\bsf\s+data\s+(?!query\b|get\b|search\b|export\b)\w+", s):
        return org_write(s, "sf data write")
    if re.search(r"\bsf\s+apex\s+run\s+test\b", s):
        kind = org_kind(target_org(s))
        return (ALLOW, "apex tests") if kind in ("build", "qa") else (DENY, "apex tests: build/qa orgs only")
    if re.search(r"\bsf\s+apex\s+run\b", s):
        return org_write(s, "anonymous Apex")
    if re.search(r"\bsf\s+api\s+request\s+rest", s):
        m = re.search(r"(?:-X|--method)(?:\s+|=)['\"]?(\w+)", s)
        if (m and m.group(1).upper() not in ("GET", "HEAD")) or re.search(r"(?:^|\s)(-b|--body)\b", s):
            return org_write(s, "REST write")
        return ALLOW, "REST GET"
    if re.search(r"\bsf\s+config\s+(set|unset)\s+target-org", s):
        if re.search(r"\bunset\b", s) or re.search(rf"target-org[=\s]+{re.escape(BUILD_ALIAS)}\b", s):
            return ALLOW, "global target-org = build org (deploy-gate workaround)"
        return DENY, f"global target-org may only be set to {BUILD_ALIAS}"
    if re.search(r"\bgh\s+pr\b", s) and not re.search(r"\bgh\s+pr\s+(view|list|checks|diff|status)\b", s):
        return DENY, "PRs are opened by the orchestrator after the operator's OK"
    if re.search(r"\bgit\b", s):
        if re.search(r"\bgit(\s+-C\s+\S+)*\s+(push|merge|pull|rebase|cherry-pick|revert|tag)\b", s) or \
           re.search(r"\breset\s+--hard\b|\bclean\s+-\w*f|\bbranch\s+-D\b|\bstash\s+(drop|clear)\b", s):
            return DENY, "builder never pushes/merges/rewrites history"
        if re.search(rf"\b(checkout|switch)\s+(origin/)?{re.escape(BRANCH)}\b", s):
            return DENY, f"builder never checks out {BRANCH}"
        if re.search(r"\bworktree\s+add\b", s):
            return (ALLOW, "worktree add") if WORKTREE_RE.search(s) and f"origin/{BRANCH}" in s else \
                   (DENY, f"worktree must be ../{REPO_NAME}-<KEY> off origin/{BRANCH}")
        if re.search(r"\bworktree\s+(remove|prune)\b", s):
            return DENY, "worktree removal is the operator's call"
        if re.search(r"\b(commit|add|rm|mv|restore|checkout|switch|stash|apply|am)\b", s):
            repo = git_repo_path(s)
            if repo == REPO:
                return DENY, f"never modify the main {REPO_NAME} checkout; use the worktree"
            if WORKTREE_RE.search(repo):
                return ALLOW, "git in worktree"
            return DEFER, "git write outside known repo"
    d, r = classify_readonly(s)
    # Read-only rules deny writes; for the builder only the protected-path/rm/http rules still apply.
    if d == DENY and not re.search(r"\b(sf|git|gh)\b", s):
        return d, r
    return (d if d != DENY else DEFER), r


if tool == "Bash":
    emit(*bash_decision(ti.get("command", ""), classify_builder))

if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    d, r = classify_write_path(path, [CASES])
    if d == DENY and WORKTREE_RE.search(os.path.realpath(path)) and "approved.json" not in path:
        d, r = ALLOW, "write in worktree"
    emit(DEFER if d == ALLOW else d, r)

emit(DEFER, "not guarded")
