# Design decisions

Why the workflow looks the way it does. Each decision came from a real failure or a near-miss.

## One entry point, fixed phases
`/sf-ticket <anything>` always runs the same nine phases. The **lane** (support, explain, change,
bug, gtm) only decides which phases to skip. A fixed loop is easier to trust, resume and audit
than an agent that plans its own route each time.

## Find is separate from fix
Four agents are read-only, and a hook enforces it. Only `sf-builder` changes metadata, and only
in the build org and its own worktree. Investigators that can't write can't "fix while looking",
which is when undocumented changes happen.

## Guardrails are code, not prose
Prompts restate the rules, but PreToolUse hooks enforce them:
- read-only agents: no deploys, data writes, anonymous Apex, non-GET REST, git writes, or writes
  outside the case folder
- builder: build org allowed, QA org asks, Prod and unrecognised orgs denied, missing `-o` denied
- QA: test-record writes only, never metadata, never Prod

The test suite in `tests/` checks each rule with real tool-call payloads.

## Approval is a hash, not a status
The operator approves the spec in the terminal. The orchestrator writes `approved.json` with the
SHA-256 of `spec.md`, and the builder's hook refuses to deploy unless the hash still matches. Edit
the spec after approval and the build stops until it's approved again. A Jira transition never
counts as approval, because anyone can click one.

## An adversarial verifier
`sf-verifier` runs on Opus with one job: find what's wrong. It re-runs every query itself, marks
claims CONFIRMED / PLAUSIBLE / REFUTED, tests the root cause against a fixed list of alternatives
(inactive flow version, save order, FLS, drift, recent deploy, bypass settings, managed packages),
and must report at least one weakness. In the pilot, the org check overturned intake's reading of
an ambiguous "mirror this user" request.

## Files, not chat
Every ticket gets a case folder. Agents write `intake.md`, `org.md`, `repo.md`, `verdict.md`,
`build.md`, `review.md`, `qa.md` and return five lines plus a path. The orchestrator's context
stays small, any phase can be resumed, and the folder is the audit trail. `case.md` holds phase
checkboxes, retry counters, decisions and every Prod write with before → after values.

## Humans own the outward and irreversible steps
Every Jira write, Confluence page, Slack message, Gearset PR and Prod change is a ⏸ gate. One OK
covers one action. Agents can't take these actions at all: the tools are in their
`disallowedTools`.

## Complex flows go to a human
Generated Flow XML has known defects (lost variable wiring, dropped `runInMode`, no subflows).
For anything beyond a small linear flow, the builder writes a Flow Builder checklist instead of
XML. The rule is: if a human can't verify the diff, a human builds it.

## Right-sized models
Intake and the repo investigator run on Sonnet (reading and summarising). The org investigator,
builder and QA inherit the session model. The verifier runs on Opus, because finding faults is
the hardest reasoning in the loop.

## Lessons compound
`sf-gotchas.md` holds 30 rules, each with the incident that taught it. Agents are told to report
new non-obvious lessons, and the close phase proposes adding them. Agents with `memory: user`
keep their own notes on recurring patterns, but never ticket facts.

## Not in v1
- Unattended runs (a scheduled intake-only pass over new support tickets that drafts but never
  sends).
- Builds for the gtm lane: CPQ and pricing work has ERP dependencies no agent can verify.
- A dashboard built from case-file frontmatter.
