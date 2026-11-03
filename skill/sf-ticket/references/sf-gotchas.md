# Salesforce gotchas — rules learned the hard way

Each rule is followed by the reason. Read before touching an org. When you learn a new,
non-obvious lesson, tell the orchestrator in your return summary so it can be added here.
Org-specific traps belong in `org-profile.md`; this file is for lessons that hold in any org.

## Access and tooling

1. **If the `salesforce-development` plugin is installed, `sf data query` and
   `sf project retrieve start` may be hook-blocked** by its "skills-first enforcement".
   - Read data with `sf api request rest "/services/data/v64.0/query/?q=…" -o <alias>`, or an
     MCP connector.
   - Read metadata with `.../tooling/query/?q=…`. See query-recipes.md.
2. **Salesforce MCP connectors usually only see data.** They cannot see ValidationRule, Flow,
   Apex, layouts or FLS. "No automation found" from an MCP query means NOT CHECKED. It does not
   mean absent.
3. **The Tooling API refuses `SELECT Metadata` when more than one row matches.** Loop one Id at
   a time.
4. **`sf api request rest` prints a beta warning to stderr.** Use `2>/dev/null` and parse JSON
   with `python3 -c` or `jq`.
5. **`CustomField.TableEnumOrId` stores the `01I` Id for custom objects.** Filtering it by API
   name silently returns zero rows. Use `EntityDefinition.QualifiedApiName` relationships, or
   resolve the Id first.
6. **A plugin deploy-gate may need a global target-org.** If `sf project deploy` is blocked with
   "No target org is configured":
   - In a worktree, run `sf config set target-org <build alias> --global`, deploy, then
     `sf config unset target-org --global`.
   - Never leave a global default behind. The builder guard only allows the build alias here.
7. **Generated Flow XML is NOT deploy-safe** (gotcha 14), whichever generator produced it.

## Before changing anything

8. **Query existing automation on the object every time, not once per session.** A past ticket
   duplicated two validation rules that already existed; one had been created earlier the same
   day by a parallel session. Prefer extending an existing rule over adding a parallel one.
9. **Save order matters:** VR → before-save flow → before trigger → after trigger →
   after-save flow → async. List every automation on the object in that order before
   claiming a root cause.
10. **Always check the ACTIVE flow version (FlowDefinition.ActiveVersion), not the latest.**
    A deploy can leave the newest version as a Draft while an older one stays active.
11. **Don't narrow a shared flow's entry criteria to fix one case.** Other branches depend on it.

## Building and deploying

12. **Build in the build sandbox first, always.** Path: build → QA → Prod. The QA org is the
    independent QA environment, and building there first contaminates it. The exception is CPQ
    config and data fixes in QA, which are allowed with a prompt.
13. **Dry-run first. New automation deploys INACTIVE to every org on its first deploy,** even if
    the spec or file says active. Shipping new VRs active once could have blocked most edits on
    a busy object.
    - "Succeeded" is not evidence. Re-query the actual state with the Tooling API.
14. **Generated Flow XML bugs seen in practice:**
    - Get Records outputs are auto-stored, while later elements read SObject variables that
      were never populated.
    - Bogus `outputAssignments` are added.
    - `runInMode` is dropped.
    - The flow is labelled "Start".
    - `isAdditionalPermissionRequiredToRun` is never set.
    - `<subflows>` and `<actionCalls>` can't be emitted.
    - A passing dry-run does NOT mean the logic is right. Complex flow edits go to the operator
      as a Flow Builder checklist.
15. **Setting a flow's status to `Obsolete` silently does nothing.** The deploy says Succeeded
    and the flow stays Active. Deactivate with a FlowDefinition component
    (`<activeVersionNumber>0</activeVersionNumber>`). Deleting a flow may then fail with
    `insufficient access rights on cross-reference id`.
16. **Put FLS in permission sets, not profiles.**
    - Full-profile deploys to sandboxes fail on drift. Use trimmed profiles only if unavoidable,
      and note it.
    - Gearset diffs drag in dozens of profiles whenever FLS changes.
17. **Permission set assignments are DATA, not metadata.** List them under Post Deployment
    Steps.
18. **System-context flows bypass FLS.** Screen flows can't run in system context.
    Setup-object DML (User, PermissionSetAssignment) in the same transaction as other DML →
    `MIXED_DML_OPERATION`.
19. **A flow's label and its API name often differ.** Search for both.
20. **Prefer a validation rule over Apex** for simple constraints. Every PR's contents must
    deploy and revert together.
21. **Standards:**
    - Use `sf`, never `sfdx`.
    - Pass an explicit `-o` on every command.
    - No DML or SOQL in loops.
    - Put a LIMIT on every query.
    - Flows need fault paths.
    - Never hardcode Ids.

## Specific traps

22. **A Flow Get Records filtering `Id` on a non-Id string throws** `FlowException` before the
    query runs, even when OR'd with another filter. Apex SOQL binds do NOT throw, so the bug is
    invisible from anonymous Apex.
    - To reproduce: deploy a disposable autolaunched probe flow and call it via
      `Flow.Interview`.
    - Fix: classify by LEN() = 15 or 18, branch, then TRIM().
23. **User deactivation blockers:**
    - `DEPENDENCY_EXISTS`: the user is an email-alert recipient.
    - `cannot inactivate assignee of a case rule entry`: this applies even when the
      assignment rule is inactive.
    - Find blockers by retrieving Workflow + AssignmentRules and grepping for the username.
    - Blockers differ per org.
    - Bot users can carry an employee's `+alias` email. Don't deactivate those; re-point them
      instead.
    - Sweep `Email` and `Username` too, not just Name.
24. **Prod QA records:** follow the test-record conventions in org-profile (a `Test - <KEY>` name,
    the org's test-data flag, and stages or statuses to avoid because they fire alerts).
25. **Long-text fields can't be used in a SOQL `WHERE … LIKE`.** Query by date and filter on
    the client side.
26. **One-record-per-call MCP writes can't reproduce bulk or governor-limit bugs.** Say so as a
    caveat.
27. **Mirror and "align" requests are often ambiguous about direction.** On one pilot ticket
    the description read as "A → B", an AI-generated triage comment said "B → A", and the audit
    trail showed it had already been worked B → A. Neither the text nor the bot is reliable
    alone. Confirm the direction with the requester (or the operator), and check
    SetupAuditTrail for whether someone already acted.
28. **SetupAuditTrail:**
    - `Display` and `Section` can't be filtered in WHERE (INVALID_FIELD).
    - Filter by `CreatedDate` and/or `CreatedById`, use LIMIT 2000, and match Display in python.
    - A busy Prod org easily returns 2000 rows for 30 days.
29. **PermissionSetAssignment has no CreatedDate.** Use `SystemModstamp`. A profile-owned
    assignment's SystemModstamp changes when the user's profile changes, which is a useful
    signal.
30. **Name searches on User hit portal and duplicate users first.** A pilot ticket turned up
    two portal users with the same name as the real employee. Filter `UserType='Standard'` for
    the main pass, then run one unfiltered pass on `Email`/`Username` to catch `+alias` portal
    or bot users.
