# Build — SF-142

- Worktree: `~/code/salesforce-SF-142`, branch `SF-142/region-on-renewals`, commit `a41c9e2`
- Pre-check: no other flow or trigger writes `Region__c` (re-queried dev).

## Metadata Components Changed
| Type | API name | Change |
|---|---|---|
| Flow | `Opp_Set_Region` | v8: CreateAndUpdate, entry criteria Region blank and AccountId set |

## Deploys
- Dry-run `0AfXX00000DRY01`: succeeded.
- Deploy `0AfXX00000DEP01`: succeeded. Verified by Tooling: v8 status **Draft**, v6 still active.

## Activation pending
- Activate v8 in dev for QA (brief says yes), then in each org after promotion.

## Post Deployment Steps
1. Activate `Opp_Set_Region` v8.
2. Backfill Region on the 37 renewals.

## Not verified
- None beyond spec.

## Questions for the operator
- None.
