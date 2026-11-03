# Taking it to a new company

Everything company-specific lives in **two files**. The skill, agents, templates and hooks don't
change between orgs.

| File | Read by | Holds |
|---|---|---|
| `skill/sf-ticket/config.json` | the guard hooks | cases dir, repo path, default branch, org-alias patterns, protected paths |
| `skill/sf-ticket/references/org-profile.md` | the orchestrator and every agent | orgs and usernames, Gearset pipeline Ids, Jira projects and statuses, Confluence space, Slack channels, routing, key objects, test-record conventions, cadence |

## Checklist for a new org

1. **Orgs.** Authenticate `sf` to three orgs and pick aliases (e.g. `dev`, `qa`, `prod`). Put the
   build and QA aliases and username patterns in `config.json → orgs`. Anything that doesn't
   match is treated as Prod by the hooks, so a typo fails safe.
2. **Repo.** Set `repo_path` and `default_branch`. Worktrees are created next to it as
   `<repo name>-<KEY>`.
3. **Gearset.** Copy the pipeline and environment Ids into org-profile.
4. **Jira.** Name the change project and the support project, their statuses, how support
   tickets are closed, and any custom fields you use.
5. **Confluence.** Name the space to search for prior art and the parent pages for release
   notes and how-to answers.
6. **Slack.** List the intake, request, error-alert and routing channels with their Ids.
7. **Conventions.** Bypass settings, the test-data flag, managed packages never to edit,
   integrations no agent can verify, Prod test-record rules, deployment window.
8. **Protected paths.** Anything agents must never write to (a notes vault, a shared drive).
9. **Lanes.** If the org has its own support types (entitlements, licensing), add rows to the
   support-type table in `lanes.md`.
10. **Pilot** on two closed tickets: one support, one bug.

## MCP tool names

Agent `disallowedTools` lists use the tool names of the Claude.ai Atlassian and Slack connectors
(`mcp__claude_ai_Atlassian_MCP__*`, `mcp__claude_ai_Slack__*`) and a Gearset server registered as
`gearset`. If your connectors register under other names, update the lists in `agents/*.md`:

```bash
sed -i '' 's/mcp__claude_ai_Atlassian_MCP__/mcp__atlassian__/g' agents/*.md
```

If you add a Salesforce MCP server with write tools, add those write tools to every read-only
agent's `disallowedTools`. The hooks guard `sf` CLI calls; MCP writes are blocked by the tool
lists and the orchestrator's ⏸ gates.

## What stays out of the repo

`.gitignore` excludes `config.json`, `org-profile.md` and case folders. Case files hold real
ticket content and Prod record Ids; keep them on your machine.
