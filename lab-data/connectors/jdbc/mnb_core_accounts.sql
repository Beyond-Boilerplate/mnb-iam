-- Meridian lab schema + seed for JDBC connector lessons (PostgreSQL)
-- Applied on first init of jdbc-pg via docker-entrypoint-initdb.d

CREATE TABLE IF NOT EXISTS mnb_app_accounts (
  account_id   VARCHAR(64) PRIMARY KEY,
  username     VARCHAR(128) NOT NULL,
  email        VARCHAR(256),
  employee_id  VARCHAR(32),
  status       VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  entitlement  VARCHAR(64),
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mnb_app_entitlements (
  entitlement_code VARCHAR(64) PRIMARY KEY,
  display_name     VARCHAR(128) NOT NULL,
  risk_tier        VARCHAR(16) NOT NULL
);

INSERT INTO mnb_app_entitlements (entitlement_code, display_name, risk_tier) VALUES
  ('WIRE_INIT', 'Wire Portal — Initiate', 'critical'),
  ('WIRE_APPR', 'Wire Portal — Approve', 'critical'),
  ('SAP_FI', 'SAP Finance', 'critical'),
  ('DWRP', 'Dev Workstation / Repo', 'medium')
ON CONFLICT (entitlement_code) DO NOTHING;

INSERT INTO mnb_app_accounts (account_id, username, email, employee_id, status, entitlement) VALUES
  ('jdbc-001', 'priya.wire', 'priya.wire@meridiannb.com', 'MNB00090', 'ACTIVE', 'WIRE_INIT'),
  ('jdbc-002', 'marcus.approve', 'marcus.approve@meridiannb.com', 'MNB00091', 'ACTIVE', 'WIRE_APPR'),
  ('jdbc-003', 'jordan.reed', 'jordan.reed@meridiannb.com', 'MNB00092', 'ACTIVE', 'SAP_FI'),
  ('jdbc-004', 'samir.hassan', 'samir.hassan@meridiannb.com', 'MNB00094', 'DISABLED', 'DWRP')
ON CONFLICT (account_id) DO UPDATE SET
  username = EXCLUDED.username,
  email = EXCLUDED.email,
  employee_id = EXCLUDED.employee_id,
  status = EXCLUDED.status,
  entitlement = EXCLUDED.entitlement,
  updated_at = CURRENT_TIMESTAMP;
