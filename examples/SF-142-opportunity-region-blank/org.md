# Org findings — SF-142

| | |
|---|---|
| Agent | sf-org-investigator |
| Org(s) asserted | prod = ops@acme.example (00DXX0000001PROD), dev = ops@acme.example.dev (00DXX0000002DEV0) |
| Repo commit | n/a |
| Run at | 2026-09-14 09:29 |

## Summary (≤5 lines)
`Opp_Set_Region` is a before-save flow that runs **on create only**. Since SF-131, `Renewal_Create`
inserts the renewal without AccountId and sets it in a second update, so the region flow sees no
Account. 37 renewals in Prod are blank. Account Region is populated on all 37 Accounts.

## Claims
| # | Claim | Evidence | Confidence |
|---|---|---|---|
| 1 | 37 renewals since 2026-08-25 have blank Region | `Q "SELECT+COUNT()+FROM+Opportunity+WHERE+Type='Renewal'+AND+Region__c=null+AND+CreatedDate>=2026-08-25T00:00:00Z"` → 37 | high |
| 2 | Accounts on those renewals have a Region | same set joined to Account → 37/37 non-blank | high |
| 3 | Active version of `Opp_Set_Region` is v6, RecordTriggerType = Create | `FlowDefinitionView` → ActiveVersionId 301XX…v6; Flow v6 Metadata.start.recordTriggerType = Create | high |
| 4 | `Renewal_Create` v12 inserts without AccountId, then updates it | Flow v12 Metadata: recordCreates has no AccountId; recordUpdates sets AccountId | high |

## Automation inventory (save order) — Opportunity
| Order | Type | API name | Active version / status | Touches in-scope fields? |
|---|---|---|---|---|
| 1 | Validation rule | `Region_Required_On_Close` | Active | reads Region__c |
| 2 | Before-save flow | `Opp_Set_Region` | v6 Active (Create only) | writes Region__c |
| 3 | After-save flow | `Renewal_Create` (on Contract) | v12 Active | writes AccountId |

## Gaps
- Error-log object: none relevant in the window.

## Surprises
- VR `Region_Required_On_Close` will block closing these 37 renewals once reps try to close them.
