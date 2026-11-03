"""Positive and negative tests for the guard hooks. Run: python3 -m unittest discover tests"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks")


class GuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="sfguard-")
        # Keep the fixture out of tmp so the hooks' "tmp is always writable" rule doesn't mask results.
        cls.root = os.path.realpath(os.path.join(os.path.expanduser("~"), ".sfguard-test"))
        cls.cases = os.path.join(cls.root, "cases")
        cls.repo = os.path.join(cls.root, "code", "salesforce")
        cls.notes = os.path.join(cls.root, "Notes")
        cls.worktree = os.path.join(cls.root, "code", "salesforce-SF-142")
        cls.case = os.path.join(cls.cases, "SF-142-opportunity-region-blank")
        for d in (cls.case, cls.repo, cls.notes, cls.worktree):
            os.makedirs(d, exist_ok=True)
        cls.config = os.path.join(cls.tmp, "config.json")
        with open(cls.config, "w") as f:
            json.dump({"cases_dir": cls.cases, "repo_path": cls.repo, "default_branch": "main",
                       "protected_paths": [cls.notes],
                       "orgs": {"build": ["dev", "*.dev"], "qa": ["qa", "*.qa"]}}, f)
        cls.approve("## Changes\n1. Add VR\n")

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.root, ignore_errors=True)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def approve(cls, spec):
        with open(os.path.join(cls.case, "spec.md"), "w") as f:
            f.write(spec)
        h = hashlib.sha256(spec.encode()).hexdigest()
        with open(os.path.join(cls.case, "approved.json"), "w") as f:
            json.dump({"sha256": h}, f)

    def run_hook(self, hook, tool, tool_input, cwd=None):
        env = dict(os.environ, SF_TICKET_CONFIG=self.config)
        payload = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or self.root}
        out = subprocess.run([sys.executable, os.path.join(HOOKS, hook)], input=json.dumps(payload),
                             capture_output=True, text=True, env=env, check=True).stdout.strip()
        if not out:
            return "defer"
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]

    def bash(self, hook, cmd, cwd=None):
        return self.run_hook(hook, "Bash", {"command": cmd}, cwd)

    # ---- read-only agents ----
    def test_readonly_blocks_org_writes(self):
        r = "sf-readonly-guard.py"
        self.assertEqual(self.bash(r, "sf data update record -s Account -i 001 -v 'Name=x' -o dev"), "deny")
        self.assertEqual(self.bash(r, "sf project deploy start --source-dir force-app -o dev"), "deny")
        self.assertEqual(self.bash(r, "sf apex run -f x.apex -o dev"), "deny")
        self.assertEqual(self.bash(r, "sf api request rest /services/data/v64.0/sobjects/Account -X POST -o prod"), "deny")
        self.assertEqual(self.bash(r, "sfdx force:org:list"), "deny")

    def test_readonly_allows_reads(self):
        r = "sf-readonly-guard.py"
        self.assertEqual(self.bash(r, "sf api request rest '/services/data/v64.0/tooling/query/?q=SELECT+Id+FROM+Flow' -o prod 2>/dev/null"), "defer")
        self.assertEqual(self.bash(r, f"git -C {self.repo} log -5 origin/main"), "defer")
        self.assertEqual(self.bash(r, "sf org display -o prod --json | jq .result.username"), "defer")

    def test_readonly_blocks_git_and_protected(self):
        r = "sf-readonly-guard.py"
        self.assertEqual(self.bash(r, f"git -C {self.repo} push origin main"), "deny")
        self.assertEqual(self.bash(r, f"git -C {self.repo} checkout -b x"), "deny")
        self.assertEqual(self.bash(r, f"echo hi > {self.notes}/x.md"), "deny")
        self.assertEqual(self.run_hook(r, "Write", {"file_path": f"{self.notes}/x.md"}), "deny")
        self.assertEqual(self.run_hook(r, "Write", {"file_path": f"{self.case}/approved.json"}), "deny")
        self.assertEqual(self.run_hook(r, "Write", {"file_path": f"{self.root}/elsewhere.md"}), "deny")
        self.assertEqual(self.run_hook(r, "Write", {"file_path": f"{self.case}/org.md"}), "defer")

    # ---- builder ----
    def test_builder_org_tiers(self):
        b = "sf-builder-guard.py"
        wt = self.worktree
        self.assertEqual(self.bash(b, "sf project deploy start --dry-run --source-dir force-app -o dev", wt), "allow")
        self.assertEqual(self.bash(b, "sf project deploy start --source-dir force-app -o dev", wt), "allow")
        self.assertEqual(self.bash(b, "sf project deploy start --source-dir force-app -o qa", wt), "ask")
        self.assertEqual(self.bash(b, "sf project deploy start --source-dir force-app -o prod", wt), "deny")
        self.assertEqual(self.bash(b, "sf project deploy start --source-dir force-app -o me@acme.com", wt), "deny")
        self.assertEqual(self.bash(b, "sf project deploy start --source-dir force-app", wt), "deny")
        self.assertEqual(self.bash(b, "sf data update record -s Account -i 001 -v 'Name=x' -o me@acme.com.dev", wt), "allow")

    def test_builder_needs_matching_approval(self):
        b = "sf-builder-guard.py"
        cmd = "sf project deploy start --source-dir force-app -o dev"
        other = os.path.join(self.root, "code", "salesforce-SF-999")
        self.assertEqual(self.bash(b, cmd, other), "deny")  # no case folder
        with open(os.path.join(self.case, "spec.md"), "a") as f:
            f.write("\n2. sneaky extra change\n")
        try:
            self.assertEqual(self.bash(b, cmd, self.worktree), "deny")  # spec edited after approval
        finally:
            self.approve("## Changes\n1. Add VR\n")
        self.assertEqual(self.bash(b, cmd, self.worktree), "allow")

    def test_builder_git_rules(self):
        b = "sf-builder-guard.py"
        self.assertEqual(self.bash(b, f"git -C {self.repo} worktree add ../salesforce-SF-142 -b SF-142/Region origin/main"), "allow")
        self.assertEqual(self.bash(b, f"git -C {self.repo} worktree add ../scratch -b x origin/main"), "deny")
        self.assertEqual(self.bash(b, f"git -C {self.worktree} commit -m 'SF-142: add VR'"), "allow")
        self.assertEqual(self.bash(b, f"git -C {self.repo} commit -m 'oops'"), "deny")
        self.assertEqual(self.bash(b, f"git -C {self.worktree} push -u origin SF-142/Region"), "deny")
        self.assertEqual(self.bash(b, f"git -C {self.worktree} checkout main"), "deny")
        self.assertEqual(self.bash(b, "gh pr create --fill"), "deny")

    def test_builder_target_org_workaround(self):
        b = "sf-builder-guard.py"
        self.assertEqual(self.bash(b, "sf config set target-org dev --global"), "allow")
        self.assertEqual(self.bash(b, "sf config unset target-org --global"), "allow")
        self.assertEqual(self.bash(b, "sf config set target-org prod --global"), "deny")

    def test_builder_writes(self):
        b = "sf-builder-guard.py"
        self.assertEqual(self.run_hook(b, "Write", {"file_path": f"{self.worktree}/force-app/x.xml"}), "defer")
        self.assertEqual(self.run_hook(b, "Write", {"file_path": f"{self.case}/build.md"}), "defer")
        self.assertEqual(self.run_hook(b, "Write", {"file_path": f"{self.case}/approved.json"}), "deny")
        self.assertEqual(self.run_hook(b, "Write", {"file_path": f"{self.repo}/force-app/x.xml"}), "deny")

    # ---- QA ----
    def test_qa_tiers(self):
        q = "sf-qa-guard.py"
        self.assertEqual(self.bash(q, "sf data create record -s Opportunity -v 'Name=SF-142-QA' -o dev"), "allow")
        self.assertEqual(self.bash(q, "sf data create record -s Opportunity -v 'Name=SF-142-QA' -o qa"), "ask")
        self.assertEqual(self.bash(q, "sf data create record -s Opportunity -v 'Name=x' -o prod"), "deny")
        self.assertEqual(self.bash(q, "sf data delete record -s Opportunity -i 006 -o dev"), "deny")
        self.assertEqual(self.bash(q, "sf project deploy start --source-dir force-app -o dev"), "deny")
        self.assertEqual(self.bash(q, "sf apex run test -n RegionTest -o qa"), "allow")

    # ---- crash path: Claude Code only blocks on exit 2, so a crash must never exit 1 ----
    GUARDS = ("sf-readonly-guard.py", "sf-builder-guard.py", "sf-qa-guard.py")

    def run_raw(self, hook, stdin, config=None):
        env = dict(os.environ, SF_TICKET_CONFIG=config or self.config)
        return subprocess.run([sys.executable, os.path.join(HOOKS, hook)], input=stdin,
                              capture_output=True, text=True, env=env)

    def test_malformed_config_blocks(self):
        bad = os.path.join(self.tmp, "bad-config.json")
        with open(bad, "w") as f:
            json.dump({"orgs": ["dev"]}, f)  # a list where a dict is expected
        prod_deploy = json.dumps({"tool_name": "Bash",
                                  "tool_input": {"command": "sf project deploy start -o prod"}})
        for hook in self.GUARDS:
            p = self.run_raw(hook, prod_deploy, bad)
            self.assertEqual(p.returncode, 2, hook)
            self.assertIn("[sf-guard] guard crashed", p.stderr, hook)

    def test_unhandled_exception_blocks(self):
        bad_input = json.dumps({"tool_name": "Bash", "tool_input": "sf project deploy start -o prod"})
        for hook in self.GUARDS:
            self.assertEqual(self.run_raw(hook, bad_input).returncode, 2, hook)

    def test_unreadable_input_denies(self):
        for hook in self.GUARDS:
            for stdin in ("not json", "[]", ""):
                p = self.run_raw(hook, stdin)
                self.assertEqual(p.returncode, 0, hook)
                decision = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]
                self.assertEqual(decision, "deny", f"{hook} {stdin!r}")


if __name__ == "__main__":
    unittest.main()
