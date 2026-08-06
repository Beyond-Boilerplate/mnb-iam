# IIQ → Mailpit (Enterprise Lab)

After `./tools/lab/docker/up.sh --enterprise`:

| | |
| --- | --- |
| SMTP host (from IIQ container) | `mailpit` |
| SMTP port (inside Docker network) | `1025` |
| SMTP on host (optional tools) | `localhost:${MAILPIT_SMTP_PORT:-1026}` |
| Mail UI | http://localhost:8025/ |

## Wire IdentityIQ (learner path — Lesson 203)

1. Gear → **Global Settings** → **IdentityIQ Configuration** → **Notification Settings**.
2. SMTP Host `mailpit`, Port `1025`, Encryption none, From `iiq-noreply@meridiannb.com` → **Save**.
3. Assert: `./tools/lab/enterprise/verify-lesson.sh 203`
4. **Create** EmailTemplate `MNB-EmailTemplate-Lab-Test` (subject `Meridian lab SMTP test`) under Setup → Email Templates.
5. **Create** Rule `MNB-Rule-Send-Test-Email` with the BeanShell source from Lesson 203 (calls `context.sendEmailNotification`).
6. **Run** the rule (Debug → Run Rule, or `iiq console` → `rule MNB-Rule-Send-Test-Email`).
7. Confirm in Mailpit; re-run `verify-lesson.sh 203`.

Reference XML (optional import instead of UI create):

- `config/EmailTemplate/MNB-EmailTemplate-Lab-Test.xml`
- `config/Rule/MNB-Rule-Send-Test-Email.xml`

Optional automation (not required for the lesson):

```bash
./tools/lab/scripts/send-test-email.sh
```

## Why Mailpit

Local catch-all SMTP so approval/cert/joiner emails are visible without a real mail server.
