# Meridian IIQ plugins

IdentityIQ plugins package UI, REST endpoints, and services.

Repo examples (study structure):

- `pluginsrc/AccessRequestApprovalAddins/`
- `pluginsrc/SWECertificationsAddins/`

Enterprise checklist:

1. Manifest (`manifest.xml`) with REST/Snippets/Settings
2. Import install XML for QuickLinks / config objects
3. Version + upgrade strategy
4. SSB `plugins` build flag / image bake for homelab
5. Capability-based authorization for custom REST
6. Do not put secrets in plugin XML — use IIQ encrypted config or K8s secrets

Lesson track covers scaffolding a `mnb-iam-toolkit` plugin with one REST ping and one QuickLink.
