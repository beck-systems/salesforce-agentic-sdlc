---
ticket: <KEY>
summary: "<one line>"
lane: <support|explain|change|bug|gtm>
support_type: <user-access|permissions|data|error|cpq|integration|howto|enhancement|n/a>
outcome: <fix-now|backlog|urgent|n/a>
status: intake   # intake|investigating|verifying|spec|building|qa|promoting|done|blocked
jira_status: <To Do>
orgs: []
worktree: ""
pr: ""
linked: []       # support <-> change tickets, Confluence pages, Slack permalinks
retry_verify: 0  # max 1
retry_build: 0   # max 2
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <KEY> — <summary>

## Request
<2-sentence restated ask · requester role/team · source links>

## Phases
- [ ] 0 Open case
- [ ] 1 Intake → intake.md
- [ ] 2 Investigate → org.md / repo.md
- [ ] 3 Verify → verdict.md
- [ ] 4 Spec / plan → spec.md  ⏸ approved.json
- [ ] 5 Build → build.md, review.md
- [ ] 6 QA (build org) → qa.md
- [ ] 7 Promote → PR, QA-org QA, Prod (⏸ each)
- [ ] 8 Close

## Decisions
<!-- The operator's answers and choices, with date. Append only. -->

## Prod changes made
<!-- Every Prod write: time · object/Id · field: before → after · verified? -->

## Log
<!-- append one line per event: YYYY-MM-DD HH:MM · phase · what happened -->
