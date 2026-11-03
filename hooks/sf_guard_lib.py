"""Shared logic for the /sf-ticket PreToolUse guards (sf-readonly-guard, sf-builder-guard,
sf-qa-guard).

Each Bash command is split into segments; each segment is classified, and the most
restrictive decision wins: deny > ask > (defer) > allow. "allow" is only emitted when
every segment is explicitly allowed, so unknown commands fall through to normal permissions.

Everything company-specific (paths, repo, org aliases) comes from config.json, so the same
hooks work in any Salesforce org. See config.example.json.
"""
import fnmatch
import hashlib
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
CONFIG_PATH = os.environ.get("SF_TICKET_CONFIG") or os.path.join(
    HOME, ".claude", "skills", "sf-ticket", "config.json")

DEFAULTS = {
    "cases_dir": "~/sf-cases",
    "repo_path": "~/code/salesforce",
    "default_branch": "main",
    "protected_paths": [],
    "orgs": {
        "build": ["dev", "*.dev"],
        "qa": ["qa", "staging", "*.qa", "*.staging"],
    },
}


def load_config(path=CONFIG_PATH):
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(os.path.expanduser(path)) as f:
            user = json.load(f)
    except (OSError, ValueError):
        user = {}
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


def real(path):
    return os.path.realpath(os.path.expandvars(os.path.expanduser(path)))


CFG = load_config()
CASES = real(CFG["cases_dir"])
REPO = real(CFG["repo_path"])
BRANCH = CFG["default_branch"]
PROTECTED = [real(p) for p in CFG["protected_paths"]]
PROTECTED_RAW = [p for p in CFG["protected_paths"]] + PROTECTED
BUILD_ORGS = [p.lower() for p in CFG["orgs"]["build"]]
QA_ORGS = [p.lower() for p in CFG["orgs"]["qa"]]
BUILD_ALIAS = next((p for p in BUILD_ORGS if "*" not in p), "dev")
AGENT_MEM = os.path.join(HOME, ".claude", "agent-memory")
# Per-ticket worktrees sit next to the main checkout: <repo>-<KEY>, e.g. salesforce-SF-142
WORKTREE_RE = re.compile(re.escape(os.path.basename(REPO)) + r"-([A-Z][A-Z0-9]+-\d+)")
TMP_PREFIXES = ("/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/")

DENY, ASK, DEFER, ALLOW = 3, 2, 1, 0


def read_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def emit(decision, reason):
    if decision == DEFER:
        sys.exit(0)
    name = {DENY: "deny", ASK: "ask", ALLOW: "allow"}[decision]
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": name,
        "permissionDecisionReason": f"[sf-guard] {reason}",
    }}))
    sys.exit(0)


def segments(cmd):
    parts = re.split(r"&&|\|\||;|\n|\|", cmd)
    return [p.strip() for p in parts if p.strip()]


def target_org(seg):
    m = re.search(r"(?:^|\s)(?:-o|--target-org)(?:\s+|=)['\"]?([\w.@+-]+)", seg)
    return m.group(1) if m else None


def org_kind(alias):
    """build | qa | prod, or None when no org was passed. Unrecognised orgs count as Prod."""
    if not alias:
        return None
    a = alias.lower()
    if any(fnmatch.fnmatch(a, p) for p in BUILD_ORGS):
        return "build"
    if any(fnmatch.fnmatch(a, p) for p in QA_ORGS):
        return "qa"
    return "prod"


def under(path, root):
    p, r = real(path), real(root)
    return p == r or p.startswith(r + os.sep)


def is_tmp(path):
    p = real(path)
    return any(p.startswith(t) for t in TMP_PREFIXES)


def is_protected(path):
    return any(under(path, root) for root in PROTECTED)


# ---------- read-only classification (shared by all guards) ----------

READ_GIT = r"(fetch|log|show|diff|grep|blame|ls-files|ls-tree|rev-parse|status|cat-file|for-each-ref|describe|shortlog|merge-base|remote\s+-v|worktree\s+list|branch(\s+(-a|-r|--list|-vv?))*\s*$)"


def redirect_ok(seg):
    """True if the segment has no file redirect, or only redirects to tmp / the cases dir."""
    for m in re.finditer(r"(?:^|[^2&])>>?\s*([^&\s]+)", seg):
        tgt = m.group(1).strip("'\"")
        if not (tgt == "/dev/null" or tgt.startswith("$SCRATCH") or is_tmp(tgt) or under(tgt, CASES)):
            return False
    return True


def classify_readonly(seg):
    """Return (decision, reason) for a segment under read-only rules."""
    s = seg
    if re.search(r"\bsfdx\b", s):
        return DENY, "sfdx is not allowed; use sf"
    if re.search(r"\bsf\s+project\s+(deploy|delete|retrieve|convert|generate)", s):
        return DENY, "read-only agent: no deploy/retrieve/delete"
    if re.search(r"\bsf\s+data\s+(?!query\b|get\b|search\b|export\b)\w+", s):
        return DENY, "read-only agent: no sf data writes"
    if re.search(r"\bsf\s+apex\s+run\b", s):
        return DENY, "read-only agent: no anonymous Apex"
    if re.search(r"\bsf\s+(org\s+(create|delete|login|logout|open)|config\s+(set|unset)|alias\s+(set|unset)|package|sobject\s+create)", s):
        return DENY, "read-only agent: no org/config changes"
    if re.search(r"\bsf\s+api\s+request\s+graphql", s):
        return DENY, "read-only agent: use REST GET recipes, not graphql"
    if re.search(r"\bsf\s+api\s+request\s+rest", s):
        m = re.search(r"(?:-X|--method)(?:\s+|=)['\"]?(\w+)", s)
        if (m and m.group(1).upper() not in ("GET", "HEAD")) or re.search(r"(?:^|\s)(-b|--body)\b", s):
            return DENY, "read-only agent: sf api request rest must be GET"
        return ALLOW, "REST GET"
    if re.search(r"\bsf\s+(org\s+(list|display)|sobject\s+(describe|list)|org\s+list\s+metadata)", s):
        return ALLOW, "sf read"
    if re.search(r"\bgit\b", s):
        m = re.search(r"\bgit(?:\s+-C\s+\S+)*\s+(.*)$", s)
        sub = m.group(1) if m else ""
        if re.match(READ_GIT, sub):
            return ALLOW, "git read"
        return DENY, f"read-only agent: git '{sub.split()[0] if sub else ''}' not allowed"
    if re.search(r"\bgh\s+(pr|issue|repo|release)\s+(create|merge|close|edit|comment|delete|review)", s):
        return DENY, "read-only agent: no GitHub writes"
    if re.search(r"\b(curl|wget)\b", s) and re.search(r"(-X\s*(POST|PUT|PATCH|DELETE)|--data|-d\s|--upload)", s):
        return DENY, "read-only agent: no HTTP writes"
    if any(p in s for p in PROTECTED_RAW):
        if re.search(r"(>|\btee\b|\bmv\b|\bcp\b|\brm\b|\bsed\s+-i|\btouch\b|\bmkdir\b)", s):
            return DENY, "agents never write to protected paths"
    if re.search(r"(^|\s)rm\s", s):
        paths = [t for t in s.split()[1:] if not t.startswith("-")]
        if not paths or not all(is_tmp(p) or under(p, CASES) for p in paths):
            return DENY, "read-only agent: rm only allowed in tmp/scratch"
    if re.match(r"^(ls|cat|head|tail|wc|rg|grep|jq|find|echo|date|pwd|sort|uniq|cut|tr|awk|diff|basename|dirname|stat|file|which)\b", s):
        if not redirect_ok(s):
            return DEFER, "redirect"
        return ALLOW, "shell read"
    if re.match(r"^python3\s+-c\b", s) or re.match(r"^python3\s+-I\b", s):
        return DEFER, "python"
    return DEFER, "unclassified"


def classify_write_path(path, allow_roots):
    if not path:
        return DEFER, "no path"
    if os.path.basename(path) == "approved.json":
        return DENY, "only the orchestrator (on the operator's approval) writes approved.json"
    if is_protected(path):
        return DENY, "agents never write to protected paths"
    if is_tmp(path) or under(path, AGENT_MEM) or any(under(path, r) for r in allow_roots):
        return ALLOW, "write in allowed scope"
    return DENY, f"write outside allowed scope: {path}"


def bash_decision(cmd, classify):
    """Classify every segment of a Bash command; the most restrictive decision wins."""
    worst, why = ALLOW, "all segments allowed"
    for seg in segments(cmd):
        d, r = classify(seg)
        if d > worst:
            worst, why = d, r
        if d == DENY:
            break
    return worst, why


# ---------- approval (builder) ----------

def ticket_key(seg, cwd):
    for text in (seg, cwd or ""):
        m = WORKTREE_RE.search(text)
        if m:
            return m.group(1)
    return None


def case_dir(key):
    if not os.path.isdir(CASES):
        return None
    for name in sorted(os.listdir(CASES)):
        if name == key or name.startswith(key + "-"):
            return os.path.join(CASES, name)
    return None


def approval_ok(key):
    if not key:
        return False, f"can't tell which ticket this is: run from the {os.path.basename(REPO)}-<KEY> worktree"
    d = case_dir(key)
    if not d:
        return False, f"no case folder for {key} in {CASES}"
    spec, appr = os.path.join(d, "spec.md"), os.path.join(d, "approved.json")
    if not os.path.isfile(appr):
        return False, f"{key}: spec not approved yet (no approved.json). Ask the operator to approve spec.md"
    if not os.path.isfile(spec):
        return False, f"{key}: approved.json exists but spec.md is missing"
    try:
        with open(appr) as f:
            want = json.load(f).get("sha256", "")
    except Exception:
        return False, f"{key}: approved.json unreadable"
    with open(spec, "rb") as f:
        have = hashlib.sha256(f.read()).hexdigest()
    if want != have:
        return False, f"{key}: spec.md changed since approval; the operator must re-approve"
    return True, "approved"
