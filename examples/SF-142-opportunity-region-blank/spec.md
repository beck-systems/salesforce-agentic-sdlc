## Problem
Renewal Opportunities created since 2026-08-25 have a blank Region (37 in Prod), so they drop out of regional pipeline reports and will be blocked from closing by `Region_Required_On_Close`.

## Root cause
CONFIRMED (verdict.md). `Opp_Set_Region` runs on create only. Since SF-131, `Renewal_Create` creates the renewal without AccountId and sets it in a second update, so the region flow never sees an Account.

## Changes
1. `Opp_Set_Region` runs on create and update, with an entry condition so it only acts when Region is blank and AccountId is set.
2. Backfill Region on the 37 existing renewals.

## Acceptance criteria
- Given a renewal is created by `Renewal_Create`, when its Account has a Region, then the renewal's Region equals the Account's.
- Given a renewal created by hand with an Account, then Region is set.
- Regression: given a new-business Opportunity, Region is still set on create.
- Regression: given an Opportunity with Region already set, an Account change does not overwrite it.

## Fix Spec

**Goal:** Region is populated on every Opportunity that has an Account.

**Changes**
1. Flow `Opp_Set_Region`: recordTriggerType Create → CreateAndUpdate; entry criteria `Region__c = null AND AccountId != null`.

**Tests**
- QA cases 1–4 above in dev, then qa.

**Rollout:** build org (dry-run → deploy inactive → activate after QA) → Gearset PR → QA org → Prod (go-ahead required).

**Rollback:** FlowDefinition activeVersionNumber back to 6.

**Out of scope:** changing `Renewal_Create`.

## Metadata Components Changed
| Type | API name | Change |
|---|---|---|
| Flow | `Opp_Set_Region` | New version |

## Release Notes
| Area | Change | User impact |
|---|---|---|
| Opportunity | Region now fills in on renewals | Renewals appear in regional reports |

## Post Deployment Steps
1. Activate the new `Opp_Set_Region` version in Prod.
2. Backfill Region on the 37 renewals from their Accounts (orchestrator, after OK).

## Not verified
- Bulk creation of more than 200 renewals in one transaction.

## Follow-ups
- Delete the unused Draft v7 of `Opp_Set_Region`.
