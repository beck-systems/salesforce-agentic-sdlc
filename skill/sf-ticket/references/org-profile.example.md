# Org profile — Acme Corp (example)

> **This is the only file you rewrite when you take the workflow to a new company.** Copy it to
> `org-profile.md` (install.sh does this) and replace every value. Keep the headings: the skill
> and every agent read this file by section. Values in `<angle brackets>` are placeholders.
> Paths and org aliases the hooks enforce live in `config.json`; keep the two in sync.

Shared by the /sf-ticket orchestrator and every sf-* agent. Subagents cannot see the operator's
main memory, so this file is the source of truth. Verified <YYYY-MM-DD>.

## Operator

- Name / role: <your name>, Salesforce admin/developer.
- Salesforce user Id in Prod: `<005…>` (owner of Prod test records).
- Prose in the skill says "the operator": that's you.

## Orgs

| Role | `sf` alias | Username | MCP connection | Use |
|---|---|---|---|---|
| Build sandbox | `dev` | you@acme.com.dev | none | All new metadata is built and first deployed here. Data writes need no prompt. |
| QA / staging | `qa` | you@acme.com.qa | optional Salesforce MCP (sandbox) | Pre-prod QA. Writes are sometimes needed (fixes, CPQ config), and each one prompts. Never build here first. |
| Production | `prod` | you@acme.com | optional Salesforce MCP (read-only) | Reads are fine. Writes only from the orchestrator session, after the operator's per-change OK. |

- Assert the org by username (`sf org display -o <alias> --json`), never by a connector's
  nickname. Connector names drift between people and sessions.
- API version used by the recipes: `v64.0`.
- Promotion path: **dev → integration → qa → production**.

## Repo

- `~/code/salesforce` (GitHub `<org>/<repo>`, default branch `main`). Must match `config.json`.
- **The main checkout may be on another branch with uncommitted work. Never pull, checkout or
  reset in it.** Read with `git fetch -q`, then `git show origin/main:<path>` /
  `git grep <term> origin/main -- force-app`.
- Per-ticket worktree: `~/code/salesforce-<KEY>` on branch `<KEY>/<Slug>`, off `origin/main`.
- Gearset turns a pushed branch into one PR per pipeline stage.
- Code review: <who reviews PRs and how they're requested>.

## Gearset

- Pipeline Id: `<pipeline-id>`.
- Environment Ids: dev `<env-id>` → integration `<env-id>` → qa `<env-id>` → production `<env-id>`.
- To open a PR: push the `<KEY>/<Slug>` branch, then `create_pipeline_pull_request` targeting the
  first stage. Orchestrator only, after the operator's OK.
- Gearset can promote **record data** as well as metadata (e.g. Product2 rows). Name the changed
  records so they're included rather than replaying data fixes by hand.
- Note any Gearset MCP tools that misbehave here, with the workaround.

## Jira

- Site `<acme>.atlassian.net`, cloudId `<cloud-id>`.

| Project | Use | Statuses |
|---|---|---|
| **SF** (change project) | All new Salesforce build work | To Do → In Progress → Testing → Ready For Prod → Done |
| **SUP** (support project, JSM) | Requests from the support channel | Closed with a category (see below) |

- Support closing: <how a ticket is closed, e.g. a `!close <category>` comment command, or the
  "Resolve" transition with the Category field>. Categories: `user`, `data`, `error`, `cpq`,
  `integration`, `other`.
- Useful fields: story points `<customfield_…>`, sprint `<customfield_…>`, QA engineer
  `<customfield_…>`.
- QA sub-task convention: <e.g. a `[QA] <summary>` sub-task>.
- JQL that works well: `project in (SF,SUP) AND summary ~ "<term>" ORDER BY updated DESC` first.
  `text ~` is noisy for plain-English phrases. Read tickets in full view so comments are included.
- AI-generated triage comments (e.g. "similar incidents") are hints, not sources.

## Confluence

- Space for Salesforce docs: `<SPACE>` (e.g. `SFDOCS`).
- Where to look for prior art: runbooks, design docs and release notes under `<parent page>`.
- Where to publish: release notes go under `<Release Notes page>`; how-to answers under
  `<How-to page>`. Every create or edit is ⏸-gated.

## Slack

| Channel | Id | What |
|---|---|---|
| #sf-support | `<C…>` | Main intake. A bot creates the support ticket and posts its card in the thread. |
| #sf-requests | `<C…>` | Enhancement asks → change project |
| #sf-errors | `<C…>` | Flow / Apex error alerts |
| #revops | `<C…>` | Routing for account ownership, territory and address asks |
| #deal-desk | `<C…>` | Routing for quote and SKU corrections |

## Routing table (support replies with no Salesforce change)

| Ask | Route to |
|---|---|
| Account type, region or address change | #revops |
| Quote or SKU correction | #deal-desk |
| Account hierarchy change | <form or team> |

## Key objects and switches

- Bypass setting: `<Bypass_Settings__c>` (hierarchy custom setting); users or profiles with
  `<Bypass_VR__c>` skip validation rules.
- Test-data flag: `<Test_Record__c>` on Account and Opportunity.
- Managed packages never to edit: CPQ (`SBQQ__`), <others>.
- Integrations no agent can verify: <ERP, iPaaS, marketing automation, conversation
  intelligence…>. Flag these as "unverified, owner to confirm".
- Org-specific support types (add rows to the lanes table if needed): <e.g. entitlements,
  licensing>.

## Test record conventions

- **Sandboxes:**
  - Tag records `<KEY>-QA` in Name.
  - Reuse obviously-named test parents where you can.
  - Keep the records; offer teardown, never do it automatically.
- **Prod:**
  - Name: `Test - <KEY> <case>`.
  - Set the test-data flag.
  - Owner: the operator.
  - Use dedicated test Accounts, and keep the records.
  - Stages or statuses to avoid on Prod test records: <e.g. Closed Lost, because a flow emails
    leadership on it>.

## Cadence

- Sprint length and ceremonies: <…>.
- Deployment window: <…>. Don't hardcode it in prompts.
- Prod deploys need an explicit go-ahead.
