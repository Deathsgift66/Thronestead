# Database Backup and Recovery

This document outlines how Thronestead handles database-level backups and recovery for all schema tables such as `kingdoms`, `wars` and `kingdom_resources`.

## Nightly Full Backups

- Supabase's scheduled backup system runs every night.
- Backups are exported to a Google Cloud Storage bucket.
- Each backup file is verified using a checksum after upload.

## Point-in-Time Recovery (PITR)

- PostgreSQL WAL logging is enabled with Supabase PITR.
- Daily WAL snapshots are kept for seven days.
- Snapshots are copied to the same GCS bucket.

## Read Replica Failover

- A read-only replica is provisioned using the `supabase_read_only_user` role.
- If the primary database becomes unreachable the backend switches to `READ_REPLICA_URL` when available.
