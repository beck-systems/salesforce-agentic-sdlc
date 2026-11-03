# Verdict — SF-142 (FINDINGS mode)

**Root cause: CONFIRMED.** `Opp_Set_Region` only runs on create; since SF-131 the renewal is
created without an Account, so Region is never set.

| # | Claim | Verdict | My evidence |
|---|---|---|---|
| 1 | 37 blank renewals | CONFIRMED | re-ran count on prod → 37 |
| 2 | Accounts have Region (requester said blank) | CONFIRMED (requester claim REFUTED) | 37/37 Accounts non-blank |
| 3 | Active version is Create-only | CONFIRMED | v6 active; v7 exists as Draft and is also Create-only |
| 4 | Renewal sets AccountId in a second step | CONFIRMED | `git show origin/main:force-app/.../Renewal_Create.flow-meta.xml` matches org |

Alternatives tested: FLS on Region__c (Sales profile has edit: not the cause); a bypass setting
on the integration user (none set); repo/org drift on `Opp_Set_Region` (none).

**Weakness:** no evidence on renewals created by hand in the UI; QA should add one manual renewal.
