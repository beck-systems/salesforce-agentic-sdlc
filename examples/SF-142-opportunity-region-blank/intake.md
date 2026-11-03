# Intake — SF-142

**Restated ask:** Renewal Opportunities are created with a blank `Region__c`, so they are missing
from regional pipeline reporting. The requester wants Region populated like it is on new-business
Opportunities.

**Requester:** Sales Operations (role only)
**Sources:** SF-142 (full view, 3 comments) · SUP-2210 (linked support ticket) · Slack thread in #sf-support

## Lane
**bug**: automation that used to populate a field no longer does on one creation path.
Alternative considered: support/data (rejected: it's every renewal since late August, not one record).

## Claims
| # | Claim | Source |
|---|---|---|
| 1 | Renewal Opportunities created since about 2026-08-25 have a blank `Opportunity.Region__c` | requester |
| 2 | The Accounts on those renewals also have a blank `Account.Region__c` | requester (comment 2) |
| 3 | New-business Opportunities still get a Region | requester |
| 4 | Region is set by a flow on Opportunity | evidence: Confluence page "Opportunity field automation" |

## In scope
- Objects: Opportunity, Account
- Fields: `Opportunity.Region__c`, `Account.Region__c`, `Opportunity.AccountId`
- Automation: flow `Opp_Set_Region` (label "Opportunity: Set Region"), renewal creation flow `Renewal_Create`
- Example records: 006XX000004RENEW1, 006XX000004RENEW2

## Acceptance criteria
No AC in ticket. **Proposed:**
1. Given a renewal is created by `Renewal_Create`, when its Account has a Region, then the renewal's `Region__c` equals the Account's.
2. Regression: new-business Opportunities still get Region on create.
3. Existing blank renewals are backfilled.

## Missing info
None blocking. (Environment is Prod per SUP-2210; examples given.)

## Prior art
- SF-131: changed `Renewal_Create` to set AccountId in a second step (deployed 2026-08-24). Likely related.
- SF-58: original build of `Opp_Set_Region`.
- Confluence "Opportunity field automation": documents Region as "set on create from Account".

## Suggested investigation
Active vs latest version of `Opp_Set_Region`; whether it runs on update; how `Renewal_Create`
sets AccountId after SF-131.
