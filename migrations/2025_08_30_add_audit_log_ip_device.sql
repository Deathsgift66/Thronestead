-- Add IP address and device info columns to audit logs
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS ip_address text;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS device_info text;
ALTER TABLE archived_audit_log ADD COLUMN IF NOT EXISTS ip_address text;
ALTER TABLE archived_audit_log ADD COLUMN IF NOT EXISTS device_info text;
