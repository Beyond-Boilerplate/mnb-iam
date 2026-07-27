# Active Directory + IQService checklist (Meridian)

- [ ] Domain join account with least privilege documented
- [ ] IQService installed on Windows host near DCs (TLS enabled)
- [ ] IQService service account + SPN / cert plan
- [ ] IIQ Application type: **Active Directory - Direct**
- [ ] Forest/domain configuration; GC usage decided
- [ ] Account OU search DNs for employees vs contractors
- [ ] Group aggregation scope (security groups only?)
- [ ] Exchange / mailbox provisioning required? (yes/no)
- [ ] Password interception in scope? (Password Interceptor)
- [ ] Provisioning policies: create, enable, disable, move OU on leaver
- [ ] Correlation: `sAMAccountName` ↔ `userName`, `employeeID` ↔ `employeeId`
- [ ] Test plan: aggregate → correlate → create → disable → delete (lab only)

Lab-without-live-AD: complete Application shell, schema maps, provisioning policy forms, and IQService network design worksheet even if DC is unavailable.
