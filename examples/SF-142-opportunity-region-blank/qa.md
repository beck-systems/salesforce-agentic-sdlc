# QA report — SF-142 · build mode

| | |
|---|---|
| Org asserted | dev = ops@acme.example.dev (00DXX0000002DEV0) |
| Spec | spec.md (approved.json sha256 matches) |
| Build | a41c9e2 / 0AfXX00000DEP01, v8 activated for QA |

## Results
| # | Test case | Setup | Before | After | Result |
|---|---|---|---|---|---|
| 1 | Renewal via `Renewal_Create` | Contract SF-142-QA-1 on Account (Region EMEA) | — | Region__c = EMEA | ✅ |
| 2 | Manual renewal with Account | Opp SF-142-QA-2 | — | Region__c = AMER | ✅ |
| 3 | New business on create | Opp SF-142-QA-3 | — | Region__c = APAC | ✅ |
| 4 | Region already set, Account changed | Opp SF-142-QA-4 (Region AMER) → Account in EMEA | AMER | AMER | ✅ |

## Logged errors
FlowInterviewLog for the window: 4 runs, all Finished. AsyncApexJob failures: none.

## Caveats
- Bulk (200+) renewal creation not exercised from the CLI.
