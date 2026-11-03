# Query recipes

Copy-paste reads for each question. All are read-only GETs. `<alias>` is one of the org aliases in
org-profile (e.g. `dev`, `qa`, `prod`). URL-encode spaces as `+`. Run each with `2>/dev/null`.
Set the API version once in org-profile; `v64.0` is used below.

```bash
Q() { sf api request rest "/services/data/v64.0/query/?q=$1" -o "$2" 2>/dev/null; }          # data
T() { sf api request rest "/services/data/v64.0/tooling/query/?q=$1" -o "$2" 2>/dev/null; }  # metadata
```
(Shell functions don't persist between Bash calls, so define them in the same command.)

## Assert the org
`sf org display -o <alias> --json 2>/dev/null | python3 -c "import json,sys;r=json.load(sys.stdin)['result'];print(r['username'],r['id'],r['instanceUrl'])"`

## Automation on an object, in save order
| What | Query (Tooling unless noted) |
|---|---|
| Validation rules | `T "SELECT+Id,ValidationName,Active,ErrorMessage+FROM+ValidationRule+WHERE+EntityDefinition.QualifiedApiName='<Obj>'"` |
| VR formula (one at a time) | `sf api request rest "/services/data/v64.0/tooling/sobjects/ValidationRule/<Id>" -o <alias>` → `.Metadata.errorConditionFormula` |
| Record-triggered flows | `Q "SELECT+ApiName,Label,TriggerType,RecordTriggerType,ProcessType,ActiveVersionId,LatestVersionId+FROM+FlowDefinitionView+WHERE+TriggerObjectOrEventId='<Obj>'"` (data API). `ActiveVersionId` null = no active version |
| Flow versions / status | `T "SELECT+Id,Definition.DeveloperName,VersionNumber,Status,RunInMode+FROM+Flow+WHERE+Definition.DeveloperName='<Flow>'"` |
| Flow XML (one version) | `sf api request rest "/services/data/v64.0/tooling/sobjects/Flow/<301Id>" -o <alias>` → `.Metadata` |
| Apex triggers | `T "SELECT+Name,Status,UsageBeforeInsert,UsageAfterUpdate+FROM+ApexTrigger+WHERE+TableEnumOrId='<Obj>'"` (standard objects use the API name; custom objects use the `01I` Id) |
| Apex class body | `T "SELECT+Name,Body+FROM+ApexClass+WHERE+Name='<Class>'"` |

## Fields and permissions
| What | Query |
|---|---|
| Field shape and picklists | `sf sobject describe -s <Obj> -o <alias> --json > $SCRATCH/<obj>.json`. It's large, so parse it with python and never print it whole |
| Custom field exists? | `T "SELECT+Id,DeveloperName,TableEnumOrId+FROM+CustomField+WHERE+DeveloperName='<NameWithout__c>'"` |
| FLS on a field | `Q "SELECT+Parent.Label,Parent.IsOwnedByProfile,Parent.Profile.Name,PermissionsRead,PermissionsEdit+FROM+FieldPermissions+WHERE+Field='<Obj>.<Field__c>'"` |
| Object perms | `Q "SELECT+Parent.Label,PermissionsRead,PermissionsCreate,PermissionsEdit,PermissionsDelete+FROM+ObjectPermissions+WHERE+SobjectType='<Obj>'"` |

## Users and access
| What | Query |
|---|---|
| User (main pass) | `Q "SELECT+Id,Name,Username,Email,IsActive,Profile.Name,UserRole.Name,UserRoleId,UserRole.ParentRoleId,ManagerId,Manager.Name,UserType,LastModifiedDate,LastModifiedBy.Name+FROM+User+WHERE+(Name+LIKE+'%25<name>%25'+OR+Email+LIKE+'%25<alias>%25')+AND+UserType='Standard'+LIMIT+50"` |
| User (trap pass) | The same query without `UserType`, matching on `Email`/`Username` only, to catch portal, duplicate and `+alias` bot users (gotcha 30) |
| Managed-package seats | `Q "SELECT+PackageLicense.NamespacePrefix+FROM+UserPackageLicense+WHERE+UserId='<005>'"` |
| Report / dashboard folder shares | `Q "SELECT+Folder.Name,Folder.Type+FROM+FolderShare+WHERE+SharedTo='<005 or group Id>'"`. If FolderShare isn't queryable, check the user's groups, which is how folders are usually shared |
| Perm sets and groups | `Q "SELECT+PermissionSet.Name,PermissionSet.Label,PermissionSetGroup.DeveloperName,PermissionSet.IsOwnedByProfile,SystemModstamp+FROM+PermissionSetAssignment+WHERE+AssigneeId='<005>'"` (there's no CreatedDate) |
| Public groups / queues | `Q "SELECT+Group.Name,Group.Type+FROM+GroupMember+WHERE+UserOrGroupId='<005>'"` |
| Permission-set licenses | `Q "SELECT+PermissionSetLicense.MasterLabel+FROM+PermissionSetLicenseAssign+WHERE+AssigneeId='<005>'"` |
| Mirror diff | Run the perm set, group, PSL and package-license queries for both users, then diff in python. Leave out the profile-owned assignment (`IsOwnedByProfile=true`) or the counts are off by one. Output: "add X, remove Y" for **each** direction, plus profile, role and manager differences |
| OWD / sharing | `Q "SELECT+QualifiedApiName,InternalSharingModel,ExternalSharingModel+FROM+EntityDefinition+WHERE+QualifiedApiName='<Obj>'"` |

## History and errors
| What | Query |
|---|---|
| Setup changes | `Q "SELECT+CreatedDate,CreatedBy.Name,Section,Display+FROM+SetupAuditTrail+WHERE+CreatedDate=LAST_N_DAYS:30+ORDER+BY+CreatedDate+DESC+LIMIT+2000"`. Narrow with `CreatedById` or a tighter date range. Display and Section can't be filtered in WHERE, so match them in python |
| Failing async Apex | `Q "SELECT+ApexClass.Name,Status,ExtendedStatus,CreatedDate+FROM+AsyncApexJob+WHERE+Status='Failed'+AND+CreatedDate=LAST_N_DAYS:7+LIMIT+50"` |
| Flow interview runs | `Q "SELECT+FlowDeveloperName,FlowVersionNumber,InterviewStatus,CreatedDate,CreatedById+FROM+FlowInterviewLog+WHERE+CreatedDate=LAST_N_DAYS:7+AND+FlowDeveloperName='<Flow>'+LIMIT+50"`. There's no error-text field. Error text comes from the error-alert Slack channel (org-profile), the requester's screenshot, or the org's error-log object |
| Record field history | `Q "SELECT+Field,OldValue,NewValue,CreatedBy.Name,CreatedDate+FROM+<Obj>History+WHERE+ParentId='<Id>'+ORDER+BY+CreatedDate+DESC+LIMIT+50"` (Opportunity uses `OpportunityFieldHistory`) |

## Salesforce MCP (optional)
If a Salesforce MCP server is connected (see org-profile), its query tools are fine for **data**
reads. They can't see metadata (gotcha 2), so use the Tooling recipes above for automation and
permissions.
