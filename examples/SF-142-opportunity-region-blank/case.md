---
ticket: SF-142
summary: "Region is blank on renewal Opportunities"
lane: bug
support_type: n/a
outcome: n/a
status: done
jira_status: Done
orgs: [dev, qa, prod]
worktree: "~/code/salesforce-SF-142"
pr: "gs-pipeline/SF-142/region-on-renewals_-_integration"
linked: [SUP-2210]
retry_verify: 0
retry_build: 0
created: 2026-09-14
updated: 2026-09-18
---

# SF-142 — Region is blank on renewal Opportunities

> Fictional example. Org, people, Ids and ticket keys are invented to show the shape of a case.

## Request
Sales Ops reports that renewal Opportunities show a blank Region, which drops them out of the
regional pipeline dashboards. Escalated from support ticket SUP-2210.

## Phases
- [x] 0 Open case
- [x] 1 Intake → intake.md
- [x] 2 Investigate → org.md / repo.md
- [x] 3 Verify → verdict.md
- [x] 4 Spec / plan → spec.md  ⏸ approved.json
- [x] 5 Build → build.md, review.md
- [x] 6 QA (build org) → qa.md
- [x] 7 Promote → PR, QA-org QA, Prod (⏸ each)
- [x] 8 Close

## Decisions
- 2026-09-14 · Lane confirmed as bug (not support/data): affects every renewal, not one record.
- 2026-09-15 · Spec approved in terminal; approved.json written.
- 2026-09-17 · Prod go-ahead given for the Tuesday deployment window.
- 2026-09-18 · Backfill of 37 Opportunities approved as a Post Deployment Step.

## Prod changes made
- 2026-09-18 10:42 · 37 Opportunities · Region__c: blank → Account.Region__c · verified by re-query (0 blank renewals remain)

## Log
- 2026-09-14 09:10 · 0 · case opened from SUP-2210 escalation
- 2026-09-14 09:18 · 1 · intake: lane bug, 4 claims, 2 prior tickets, 1 Confluence page
- 2026-09-14 09:31 · 2 · org + repo investigators done in parallel
- 2026-09-14 09:44 · 3 · verifier: root cause CONFIRMED; requester claim 2 REFUTED
- 2026-09-15 08:55 · 4 · spec approved (sha256 830e…); posted to Jira as description
- 2026-09-15 10:20 · 5 · built in dev, deployed inactive; review: no defects
- 2026-09-15 11:05 · 6 · QA in dev: 4/4 pass
- 2026-09-16 14:00 · 7 · Gearset PR opened; QA-org QA 4/4 pass
- 2026-09-17 16:30 · 7 · Prod deploy; flow activated; verified on Test - SF-142 renewal
- 2026-09-18 10:45 · 8 · release notes posted to Jira and Confluence; SUP-2210 closed (data)
