# IIQ → Mailpit (Enterprise Lab)

After `./tools/lab/docker/up.sh --enterprise`:

| | |
| --- | --- |
| SMTP host (from IIQ container) | `mailpit` |
| SMTP port (inside Docker network) | `1025` |
| SMTP on host (optional tools) | `localhost:${MAILPIT_SMTP_PORT:-1026}` |
| Mail UI | http://localhost:8025/ |

## Wire IdentityIQ

1. Gear → **Global Settings** → **Email Settings** (wording varies by build).
2. Set:
   - Host: `mailpit`
   - Port: `1025`
   - Encryption: none / plaintext
   - From: `iiq-noreply@meridiannb.com`
3. Send test mail → open Mailpit UI and confirm.

Or set via debug console / `emailNotifier` configuration if your image uses `iiq.properties` overlays — prefer UI for Sandbox Path lessons.

## Why Mailpit

Local catch-all SMTP so approval/cert/joiner emails are visible without a real mail server.
