**Requested by:** <role/team (link the support or intake ticket)>

- **New field requested:** <N | Y, <count> (see New Field Requirements)>
- **Post-deployment backfill required:** <N | Y, <what and how many>>
- **Desired timeline:** <date / sprint>

## Story
In order to <outcome>, as a <role>, I want <capability>.

## Acceptance Criteria
1. <observable behaviour; API names in backticks; copied verbatim from the request where given>

## New Field Requirements
<"None." plus one sentence why, OR one block per field exactly like this. No table.>

### Field 1: <Label> (`<API_Name__c>`) on <Object>
- **Type:** <Text (255) | Picklist (restricted) | Checkbox (default unchecked) | Lookup(<Object>) | Formula (<return type>) | …>
- **Help text:** <exact text, or "None">
- **Required:** <No | Yes on the layout | Yes via VR `<Name>` when …>
- **Values:** <picklists only; otherwise leave this line out>
  - <Value 1> (default)
  - <Value 2>
- **Layout:** <page layout or Lightning page, section, position; read-only on the UI?>
- **Edit access:** <profiles / permission sets, e.g. permission set `Finance_Ops`>
- **Read-only access:** <profiles / permission sets, or "None">
- **Experience Cloud / partner access:** <No access | Read | Edit>
- **Populated by:** <users, flow `<Name>`, integration (see org-profile)>
- **Backfill:** <No | Yes: <records and source>>

## Technical Notes
| Profile or Permission Set | Example User | What changed? |
|---|---|---|
| <name> | <user> | <one short phrase> |

**Existing automation checked:** <from org.md: VRs/flows/triggers on the object; anything extended rather than duplicated>

## Impact On
- <reports, integrations, other flows, CPQ; "unverified, owner to confirm" where agents can't see>

## Metadata Components Changed
| Type | API name | Change |
|---|---|---|
| <Custom Field> | `<Object.Field__c>` | <New> |

## Release Notes
| Area | Change | User impact |
|---|---|---|
| <object> | <one sentence> | <one sentence> |

## Post Deployment Steps
1. <perm set assignments, backfill, activation; one action per item>

## Not verified
- <…>
