# Example: wire sailpoint.lmsapp.us through the existing Cloudflare Tunnel.
#
# In Cloudflare Zero Trust → Networks → Tunnels → (your tunnel) → Public Hostname:
#   Subdomain: sailpoint
#   Domain:    lmsapp.us
#   Type:      HTTP
#   URL:       identityiq.sailpoint.svc.cluster.local:8080
#
# Do NOT enable Cloudflare Access on this hostname for now (lab decision).
# Confirm service name after install:
#   kubectl -n sailpoint get svc
#
# Login: https://sailpoint.lmsapp.us/identityiq/login.jsf  (spadmin / admin after first boot)
