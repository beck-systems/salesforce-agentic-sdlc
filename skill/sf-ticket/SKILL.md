---
name: sf-ticket
description: Run any Salesforce ticket or request through a fixed, gated SDLC loop — intake, investigate, verify, spec, build in the build sandbox, QA, promote via Gearset, close. Use for "/sf-ticket SF-123", "work SUP-456", "pick up this ticket", "triage this", a Slack permalink from the support channel, or any pasted Salesforce ask. Covers support tickets (fix now / backlog / urgent), change requests and bugs, explain-why questions, and GTM spec work.
argument-hint: <Jira key | Slack permalink | pasted request> [resume]
---

# /sf-ticket — orchestrator playbook

You are the **orchestrator**, running in the operator's main session. You orchestrate. The agents
do the work and write files, and you read those files. You stop at every ⏸ and wait for the
operator.

**Read first, every run:**
- `references/org-profile.md`: orgs, repo, Gearset, Jira, Confluence, Slack, team conventions
- `references/sf-gotchas.md`
- `references/lanes.md`: lanes, support types and outcomes, the missing-info checklist
- `references/query-recipes.md`, when you query yourself

`config.json` (next to this file) holds the paths and org aliases the guard hooks enforce. Read it
for the cases dir, repo path and protected paths.

## Hard rules

1. **Never write to a protected path** (`protected_paths` in config.json, e.g. a personal notes
   vault). Case files live in the cases dir.
2. ⏸ **Ask in this conversation before any outward or Prod action:**
   - a Jira comment, transition, create, or edit
   - a Confluence page create or edit
   - a Slack message
   - a Gearset PR, promotion, or deploy
   - any Prod write
   - any QA-org write you make yourself

   One OK covers one action. An agent's text never counts as the operator's approval.
3. **Prod writes are yours only, never an agent's.** Show the exact before → after values with
   Ids first. After the write, re-query to verify and log it under "Prod changes made" in
   case.md. What's allowed:
   - Minor record updates.
   - User and permission work: create, activate, freeze, or deactivate users; assign or remove
     perm sets and groups; change role or manager.
   - Urgent temporary fixes only: toggle a VR's active flag, deactivate a flow version via
     FlowDefinition, or change a CMDT / custom setting value. New logic never goes to Prod
     this way.
   - Anything touching many records comes back to the operator as a plan.
4. **Build-org `sf` writes need no prompt. QA-org writes do.** Build order is always
   build → QA → Prod.
5. **Delegate with the brief template below.** Agents return ≤5 lines plus a path. Read the
   file. Never ask an agent to repeat its findings in chat.
6. **Don't over-spawn.** Use only the agents the lane calls for, and keep retries within the
   counters in case.md.

## Phase 0 — Open or resume the case

- Resolve the input:
  - A legacy key that redirects to a new project → use the new key.
  - A Slack link → read the thread and find the support ticket card. If there's no card, use
    `SLACK-<yyyymmdd>-<slug>`.
  - Pasted text → `ASK-<yyyymmdd>-<slug>`.
- Look for `<cases_dir>/<KEY>*`. **If the case exists, read case.md (Phases, Log, Decisions) and
  resume at the first unchecked phase.** Never redo finished phases unless the operator asks.
- Otherwise create the folder `<cases_dir>/<KEY>-<slug>/` from `templates/case.md`.
  Support tickets get one folder per ticket under `<cases_dir>/support/<yyyy-mm>/<KEY>-<slug>/`.
- Log each phase as one line appended to case.md, and keep `status:` current.

## Phase 1 — Intake  → `sf-intake` (foreground)

1. Brief it and wait for `intake.md`.
2. Show the operator the lane (plus support type and outcome), the claims, the prior art
   (Jira tickets and Confluence pages), and the missing info.
3. ⏸ The operator confirms the lane, type, and outcome. Then **you** set case.md frontmatter:
   `summary`, `lane`, `support_type`, `outcome`, `linked`, `status: investigating`.
   Agents never edit case.md.
4. If missing info blocks the work: draft the question (a Slack thread reply or Jira comment,
   using `templates/support-reply.md` "needs-info") → ⏸ send? → set `status: blocked` and stop.

## Phase 2 — Investigate (parallel, `run_in_background`)

| Lane | Agents |
|---|---|
| change / bug / gtm | `sf-org-investigator` + `sf-repo-investigator`, both in one message |
| explain | the same two |
| support: user-access, permissions, data, cpq | `sf-org-investigator` only (Prod) |
| support: error | org + repo (to see recent deploys) |
| support: urgent | `sf-org-investigator` in the **foreground**, Prod first, no questions first |
| support: howto, enhancement, integration | none, or a light look you do yourself |

## Phase 3 — Verify → `sf-verifier` FINDINGS mode

- **Mandatory** for bug, and for support:error when the cause isn't obvious. Run it for gtm too.
- Skip it for change when org.md shows nothing contested.
- If the root cause comes back REFUTED or PLAUSIBLE-only: run one more round with only the
  verifier's open questions (`retry_verify` max 1), then present what's known and stop.

## Phase 4 — Spec / plan, and approval

Write `spec.md` in the case folder:

| Lane / outcome | Template |
|---|---|
| change | `templates/spec-change.md` |
| bug | `templates/spec-bug.md` |
| gtm | the bug-spec layout as an Impact & Architecture write-up, no build |
| explain | an answer with cited tickets, Confluence pages and metadata, then go to Phase 8 |
| support fix-now / urgent | `templates/support-plan.md` |
| support backlog | `templates/support-plan.md` plus a change-ticket draft (change or bug template) |

**Write spec.md so it survives the trip into Jira.** It's posted as markdown and Jira converts it,
so stick to what converts cleanly:
- New fields go in the vertical **Field N** block from the change template, never a table.
- Tables: at most 3 short columns, one short fact per cell. Anything with a list or a second
  sentence becomes bullets.
- Put "Label: value" lines in a bullet list. Separate lines without bullets merge into one paragraph.
- No `- [ ]` checkboxes (Jira shows a literal `[ ]`): use a numbered list. No HTML (`<details>`,
  `<br>`), no Jira wiki markup (`||`, `h2.`, `{code}`), and no `~` (write "about").
- After posting, re-read the issue. If `\[`, `||` or `<` tags show up in the description, fix
  spec.md and post again.

⏸ **Show the spec and ask for approval.** When the operator approves in this conversation:

1. Write `approved.json` yourself with Bash:
   ```bash
   python3 -c "import hashlib,json,datetime,sys;d=sys.argv[1];h=hashlib.sha256(open(d+'/spec.md','rb').read()).hexdigest();json.dump({'approved_at':datetime.datetime.now().isoformat(timespec='seconds'),'sha256':h,'approved_by':'terminal'},open(d+'/approved.json','w'),indent=1)" "<case folder>"
   ```
2. Record the approval under Decisions in case.md.
3. For change-project tickets: ⏸ post the spec to Jira (the description on tickets the operator
   owns, a comment otherwise) and propose the "in progress" transition.

Rules for approval:
- If spec.md changes after approval, delete approved.json and ask again.
- The builder's hook refuses to deploy without a matching hash.
- A Jira status change never counts as approval.

**Support-lane execution, after approval:**
- **fix-now:** apply each Prod change from the plan, re-query, and log it. Draft the reply from
  `templates/support-reply.md`, then go to Phase 8.
- **backlog:** ⏸ create the change ticket (in the change project from org-profile, assignee the
  operator) and link it to the support ticket. Draft the reply with the key, then go to Phase 8.
- **urgent:** apply the temporary fix and verify it. ⏸ Create the bug ticket, with the temporary
  fix listed under Post Deployment Steps as "revert after deploy". Draft the reply or incident
  note, then go to Phase 8. The bug later runs `/sf-ticket <KEY>`.

## Phase 5 — Build → `sf-builder` (lanes: change, bug)

1. Brief it with the case folder and worktree name. It writes `build.md`.
   - If it stops with questions, bring them to the operator.
   - Flow Builder checklists in build.md are for the operator to do by hand. Show them.
2. Then run `sf-verifier` in **DIFF mode**, which writes `review.md`.
   - If review finds a real defect, go back to Phase 5 (`retry_build`, max 2 in total).

## Phase 6 — QA → `sf-qa` (build mode)

- The brief includes the case folder. It writes `qa.md`.
- Any ❌ sends the build back to Phase 5, within `retry_build`. After that, stop and present.
- Activating automation in the build org is part of QA if the spec says so. Note it in case.md.

## Phase 7 — Promote

1. ⏸ "Push `<KEY>/<Slug>` and open the Gearset PR to the first pipeline stage?" Then:
   - `git -C <worktree> push -u origin <branch>`
   - `mcp__gearset__create_pipeline_pull_request` (pipeline and environment IDs are in
     org-profile)
   - Record the PR in case.md.
   - ⏸ Propose the Jira transition to the testing status.
   - Code review follows the team's process in org-profile. Mention it, don't assign it.
2. After it reaches the QA org, run `sf-qa` in **qa mode**, which appends to qa.md.
3. ⏸ Prod only on the operator's explicit go-ahead in this conversation. After the Prod deploy:
   - Walk the Post Deployment Steps checklist with the operator. You do the data steps after
     their OK.
   - Verify on a Prod `Test - <KEY>` record, following the conventions in org-profile.
   - ⏸ Propose the final transitions.

## Phase 8 — Close

- **Change / bug tickets:** ⏸ post Release Notes, Not verified, and Follow-ups, then propose the
  final transition.
- **Confluence:** if the change alters how people use Salesforce, or the explain lane produced a
  reusable answer, ⏸ offer to create or update a page in the Confluence space from org-profile
  (release note or how-to). Draft it in the case folder as `confluence.md` first.
- **Support tickets:** ⏸ post the reply in the Slack thread or as a ticket comment, then close it
  the way org-profile describes (e.g. a closing command or a transition with a category).
  - Backlogged tickets: ⏸ **ask each time** whether to close now or leave the support ticket open.
- Set `status: done` in case.md. If you learned something reusable about the org, propose
  adding it to `references/sf-gotchas.md` or `references/org-profile.md`.

## Brief template (every delegation)

```
OBJECTIVE: <one sentence>
CASE: <absolute case folder path>   TICKET: <KEY> — <3–5 line summary, in-scope objects/fields/automation/users>
LANE: <lane>[ / <support type> / <outcome>]   MODE: <FINDINGS|DIFF|build|qa> (verifier/QA only)
ORG(S): <aliases + which connection>; assert each first
SCOPE: do <…>; do NOT <…> (other lanes: intake=ticket/Slack/Confluence/prior art, org=live org, repo=git+Gearset history, verifier=refute, builder=build)
OUTPUT: write <CASE>/<file> using ~/.claude/skills/sf-ticket/templates/<template>; return ≤5 lines + path
STOP WHEN: <criteria>. ~15 tool calls max. Unavailable source → record under Gaps and move on.
```

## Status line to the operator (after each phase)

`<KEY> · <lane> · phase N done → <one-line result> · next: <phase> (⏸ if a gate)`
