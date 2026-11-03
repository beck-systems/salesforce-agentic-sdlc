# Lanes

Intake proposes a lane, and the orchestrator confirms it with the operator. A lane decides which
phases run.

| Lane | When | Phases | Verifier | Builder |
|---|---|---|---|---|
| **support** | Support-project ticket, or a Slack ask from the support channel | intake (type + outcome) → investigate per type → fix-now / backlog / urgent | if the root cause isn't obvious | no |
| **explain** | "why does X happen", "how does Y work" | intake + prior art → org + repo → cited answer | only if the answer contradicts a ticket | no |
| **change** | Config story: field, picklist, FLS, layout, VR, simple flow, perm set | full loop | DIFF mode | yes |
| **bug** | Bug ticket, or a support ticket escalated to a defect | full loop | FINDINGS (mandatory) + DIFF | yes |
| **gtm** | SKU or launch epic story (CPQ, pricing, ERP, product rules) | intake + org + repo → impact and architecture spec only | FINDINGS | no (v1) |

How to pick:
- Support key, or someone blocked right now → **support**. If the requester only wants an
  explanation → **explain**.
- Bug issue type, or "stopped working" / an error in automation → **bug**.
- Story with "add / change / make" config → **change**.
- Parent epic is a GTM launch, or the work touches price rules, SKUs or ERP sync → **gtm**.
- When unsure, propose two lanes with reasons and let the operator choose.

## Support lane: type

The closing category column maps to whatever your support desk uses (see org-profile). Add
org-specific types (e.g. entitlements, licensing) in org-profile rather than here.

| Type | Close category | Investigate | Fix-now action (orchestrator, after the operator's OK) |
|---|---|---|---|
| user-access: new user, lost access, deactivation, team alignment (manager/role), mirror another user | user | User + reference user: profile, perm sets/groups, public groups, role, manager, licenses. Deactivation: blockers (gotcha 23) | Create, activate or freeze/deactivate the user. Assign or remove perm sets and groups. Set role and manager |
| permissions: "can't see or edit X" | user | `sf-org-investigator` in Prod: profile + perm set FLS/object perms, OWD/sharing, record owner, record type, layout assignment | Perm set assignment. A config change → backlog |
| data: record update or fix | data | Read the record(s) and which VR/flow will fire on save | Field updates shown as before → after |
| error: flow / VR / Apex error | error | Error text, active automation version, record state, recent deploys (`sf-repo-investigator`) | Data fix or a bypass for that record. A real defect → backlog or urgent |
| cpq: quote / approval | cpq | Quote state (signed? amendment?), price/product/approval rules, approver still active? | Record fix, or route to the deal desk |
| integration: third-party system | integration | What it touches (see the integrations list in org-profile) and who owns it | Usually routing |
| howto | other | Explain lane | Reply only |
| enhancement | other | Light check for existing fields and automation | Always backlog |

## Support lane: outcome

- **fix-now**: plan (exact changes + Ids) → ⏸ OK → orchestrator applies in Prod → re-query → draft
  reply → ⏸ → post + close.
- **backlog**: draft a change story or bug (templates) linked to the support ticket → ⏸ create →
  draft reply with the key → ⏸ **ask: close the support ticket now or leave it open**. Later, the
  change ticket runs `/sf-ticket` as change or bug.
- **urgent**: no clarifying questions. Investigate Prod now, in the foreground. Propose a
  temporary fix + the proper fix → ⏸ → orchestrator applies the temporary fix → verify → draft the
  bug ticket, with the temporary fix listed as "revert after" → ⏸ create → reply or incident
  note.
  - Allowed temporary fixes in Prod: toggle a VR's `active` flag, deactivate a flow version
    via FlowDefinition `activeVersionNumber`, or change a CMDT / custom setting value (a kill
    switch or bypass setting).
  - New logic never goes to Prod this way.

What counts as urgent: customer data exposure, revenue or billing blocked across many
users, an org-wide error, or the operator says so.

**Escalation:** if a support ticket hits a blocker that has been seen before (prior art
shows the same symptom), propose a **bug** in the change project.

**Routing replies** (no SF change): use the routing table in org-profile (e.g. account
ownership → RevOps, quote corrections → deal desk).

## Missing-info checklist (intake drafts the question for each one that's missing)

1. Which environment? Prod or a sandbox (which one).
2. An example record link or Id.
3. For access: whose access should be mirrored (a named user), and which exact field, object
   or report? **When two users are named, confirm the direction:** who is copied onto whom.
   Also confirm whether the manager and role should change too.
4. For CPQ: is the quote already signed or accepted?
5. A screenshot of the error, if one wasn't given.
6. For change/enhancement: acceptance criteria and desired timeline.

Don't ask for anything you can look up yourself. Don't take the requester's word for it:
verify the claims in the org.
