# Compatibility park

Stock SSD sample artifacts that are **not** part of the Meridian build.

| Path | Why parked |
| --- | --- |
| `ssd-stock-config/` | Sample XML from an older SSD pack; fails IIQ 8.5 XML validation |
| `ssf-java-iiq85-incompatible/` | SSF Java using removed `ObjectUtil.lockIdentity` overloads |
| `com-sailpoint-services/` | Additional services Java not needed for Meridian |
| `config-pending/` | Draft Meridian XML not ready for import |

Restore selectively when you adopt SSF or need a sample — do **not** copy wholesale back into `config/` or `src/` without validating against IIQ 8.5.

## MNB-HR Identity Mapping Configuration

This directory contains SailPoint IdentityIQ configuration files for creating identity mappings from MNB-HR (Human Resources) source system attributes to SailPoint Identity warehouse.

### Configuration Summary

The MNB-HR Identity Mapping configuration consists of several key components:

#### 1. **Application Configuration** (`config-pending/Application/`)
- `MNB-Application-HR-PLACEHOLDER.xml` - Template application configuration  
- `MNB-Application-HR.xml` - Actual application configuration (exported from IIQ UI)

#### 2. **Identity Mapping Rules** (`ssd-stock-config/Rule/`)
Complete set of application-specific identity mapping rules:
- `MNB-HR-IdentityMapping-email-rule.xml` - Email attribute mapping with validation
- `MNB-HR-IdentityMapping-name-rule.xml` - Composite name attribute (firstname + lastname)
- `MNB-HR-IdentityMapping-manager-rule.xml` - Manager relationship mapping
- `MNB-HR-IdentityMapping-department-rule.xml` - Department attribute mapping
- `MNB-HR-IdentityMapping-employeeType-rule.xml` - Employment type validation and mapping

#### 3. **Warehouse Integration** (`ssd-stock-config/Configuration/`)
- `MNB-HR-IdentityConfiguration.xml` - Identity warehouse configuration with:
  - Source-to-target attribute mappings
  - Validation rules and visibility settings
  - Sync configuration and error handling
  - MNB-HR specific settings

#### 4. **Supporting Configuration**
- `ssd-stock-config/CorrelationConfig/MNB-CorrelationConfig-HR-EmployeeId.xml`
- `ssd-stock-config/TaskDefinition/MNB-TaskDefinition-Aggregate-HR.xml`
- `ssd-stock-config/TaskDefinition/MNB-TaskDefinition-Refresh-Attributes.xml`
- `ssd-stock-config/Rule/MNB-Rule-Correlation-EmployeeId.xml`

### Configuration Mapping

| HR Source Attribute | Identity Target | Rule Type | Notes |
|-------------------|----------------|----------|-------|
| `email` | `email` | Direct mapping | Email format validation |
| `firstname` + `lastname` | `displayName` | Composite rule | Name formation logic |
| `managersAssociateID` | `manager.id` | Cross-reference | Manager relationship |
| `departmentName` | `departmentName` | Direct mapping | Department assignment |
| `employeeType`/`userType` | `employeeType` | Transformation | Validation to "Employee"/"Contractor" |
| `userId` | `userId` | Direct mapping | Primary identity attribute |
| `division` | `division` | Direct mapping | Organizational division |
| `location` | `location` | Direct mapping | Work location |

### Usage

1. **Setup**
   - Export actual MNB-HR application from IIQ UI
   - Replace placeholder with real configuration
   - Deploy rule and warehouse configuration files

2. **Test**
   - Test HR source data compatibility
   - Validate identity warehouse connectivity
   - Verify all mapping rules function correctly

3. **Deploy**
   - Configure IIQ workflows for rule execution
   - Set up sync schedules and mappings
   - Enable warehouse attribute visibility

### MNB-HR Source Data

- **Format**: CSV (DelimitedFile connector)
- **File**: `/Users/alishaghatane/iiq-lab-data/HRApplications.txt`
- **Columns**: 52 HR attributes including identity, contact, manager, and employment attributes
- **Configuration**: Header enabled, comma delimiter

### Reference

For specific configuration details, see `MNB-HR-IdentityConfiguration.xml` for mapping rules, validation, and sync settings.

---

Prefer refreshing from the official Compass SSD package matched to IdentityIQ 8.5.
