# Compatibility park

Stock SSD sample artifacts that are **not** part of the Meridian build.

| Path | Why parked |
| --- | --- |
| `ssd-stock-config/` | Sample XML from an older SSD pack; fails IIQ 8.5 XML validation |
| `ssf-java-iiq85-incompatible/` | SSF Java using removed `ObjectUtil.lockIdentity` overloads |
| `com-sailpoint-services/` | Additional services Java not needed for Meridian |
| `config-pending/` | Draft Meridian XML not ready for import |

Restore selectively when you adopt SSF or need a sample — do **not** copy wholesale back into `config/` or `src/` without validating against IIQ 8.5.

Prefer refreshing from the official Compass SSD package matched to IdentityIQ 8.5.
