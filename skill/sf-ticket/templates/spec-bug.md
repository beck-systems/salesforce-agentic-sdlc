## Problem
<what users see, since when, who's affected; example record Ids>

## Root cause
<verified cause — cite verdict.md status (CONFIRMED/PLAUSIBLE); include the specific element/rule/line>

## Changes
<numbered, plain-language list of what will change>

## Acceptance criteria
- Given <condition>, when <action>, then <observable result>.
- Regression: given <untouched path>, <still works>.

## Fix Spec

**Goal:** <one sentence>

**Changes**
1. <component — exact change>

**Tests**
- <named test / QA case → assertion>. Apex: include a 200-record bulk test.

**Rollout:** build org (dry-run → deploy inactive → activate after QA) → Gearset PR → QA org (QA steps: …) → Prod (go-ahead required).

**Rollback:** <how to revert; FlowDefinition activeVersionNumber / VR active=false / revert PR>

**Out of scope:** <…>

## Metadata Components Changed
| Type | API name | Change |
|---|---|---|

## Release Notes
| Area | Change | User impact |
|---|---|---|

## Post Deployment Steps
1. <perm set assignments, backfills, data, activation, temporary fixes to revert; one action per item>

## Not verified
- <what couldn't be tested and why>

## Follow-ups
- <dead config, related risks, tickets to create>
