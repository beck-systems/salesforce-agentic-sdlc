# Setup

## Requirements

| Need | Why |
|---|---|
| [Claude Code](https://claude.com/claude-code) | Runs the orchestrator skill, subagents and hooks |
| Salesforce CLI (`sf`), authenticated to a build sandbox, a QA sandbox and Prod | Every org read and write goes through `sf` with an explicit `-o` |
| A Salesforce source repo in git, deployed through **Gearset** pipelines | Builds happen in per-ticket worktrees; promotion is Gearset PRs |
| **Atlassian** MCP connector (Jira + Confluence) | Tickets, prior art, specs, release notes |
| **Slack** MCP connector | Support intake threads and replies |
| **Gearset** MCP server | Deployment history and pipeline PRs |
| Python 3.9+ | The guard hooks |

Optional: a Salesforce MCP connector (data reads), and the `salesforce-development` plugin
(metadata generators the builder can use).

## Install

```bash
git clone https://github.com/beck-systems/salesforce-agentic-sdlc.git
cd salesforce-agentic-sdlc
./install.sh            # copies into ~/.claude; set CLAUDE_HOME to install elsewhere
```

Then fill in the two org-specific files (see [customizing.md](customizing.md)):

- `~/.claude/skills/sf-ticket/config.json`: paths and org aliases the hooks enforce
- `~/.claude/skills/sf-ticket/references/org-profile.md`: everything else the agents need to know

Restart Claude Code so it picks up the new agents.

## Recommended permission rules

Read-only metadata queries against Prod are routine in this workflow. Add allow rules so they
don't prompt, and leave everything else on the normal permission flow. In
`~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(sf org display:*)",
      "Bash(sf sobject describe:*)",
      "Bash(git fetch:*)",
      "Bash(git log:*)",
      "Bash(git show:*)",
      "Bash(git grep:*)"
    ]
  }
}
```

Keep `sf api request rest` on the normal prompt flow in the main session. Inside subagents the
read-only hook already denies anything that isn't a GET.

## Verify the hooks

```bash
python3 -m unittest discover tests -v
```

The suite feeds real tool-call payloads to each hook and checks the allow / ask / deny decision
for the cases that matter: Prod writes, unapproved deploys, a spec edited after approval, git
pushes, protected paths, and QA-org prompts. It also covers the crash paths: a malformed
`config.json`, input that isn't JSON, and an exception inside a guard must all block the call.

Claude Code only blocks a tool call when a hook exits with code 2. Any other non-zero exit is
reported and the call goes ahead, so each guard turns a crash into exit 2. One failure can't be
caught from inside the script: if `python3` isn't on the PATH or the hook path in an agent file is
wrong, the shell exits 127 and the call is not blocked. Run the suite after installing, and
check that the paths in `~/.claude/agents/sf-*.md` point at real files.

## First run

Pick a closed ticket and run it read-only first:

```
/sf-ticket SF-123
```

Stop after Phase 3 and compare `intake.md`, `org.md`, `repo.md` and `verdict.md` with what really
happened. That pilot is the fastest way to find gaps in your org-profile.
