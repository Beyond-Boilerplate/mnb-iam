# Rule type cheat sheet (Meridian labs)

| Rule type | When used |
| --- | --- |
| BuildMap | Delimited/JDBC row → resource object map |
| Correlation | Account → Identity matching |
| IdentityCreation | New identity defaults |
| IdentityAttribute | Computed identity attributes |
| FieldValue | Form field defaults |
| Provisioning | Customize provisioning plan |
| BeforeProvisioning / AfterProvisioning | Plan mutate / post actions |
| ResourceObjectCustomization | Tweak aggregated objects |
| Policy | Custom policy logic |
| Workflow | Workflow step logic |
| CertificationExclusion | Remove items from certs |
| Report | Custom report data |
| Listener | Lifecycle event hooks |

Stub names to create in Debug (empty body OK until lesson fills them):

- `MNB-Rule-BuildMap-HR`
- `MNB-Rule-Correlation-EmployeeId`
- `MNB-Rule-BeforeProv-AD`
- `MNB-Rule-AfterProv-Ticket`
- `MNB-Rule-IdentityAttribute-DisplayName`
