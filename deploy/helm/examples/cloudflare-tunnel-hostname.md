# Example: wire sailpoint.lmsapp.us through the existing Cloudflare Tunnel.
#
# Path split (in-cluster edge):
#   https://sailpoint.lmsapp.us/                         → Meridian IAM Academy
#   https://sailpoint.lmsapp.us/identityiq/login.jsf     → IdentityIQ
#
# In Cloudflare Zero Trust → Networks → Tunnels → (your tunnel) → Public Hostname:
#   Subdomain: sailpoint
#   Domain:    lmsapp.us
#   Type:      HTTP
#   URL:       sailpoint-edge.sailpoint.svc.cluster.local:8080
#
# IMPORTANT: Do NOT point the tunnel at identityiq.sailpoint.svc anymore.
# The edge gateway routes /identityiq → IdentityIQ and / → mnb-learn.
#
# Do NOT enable Cloudflare Access on this hostname for now (lab decision).
# Confirm services after install:
#   kubectl -n sailpoint get svc mnb-learn sailpoint-edge identityiq
#
# Deploy public surface:
#   ./learn/k8s/install-public-surface.sh
