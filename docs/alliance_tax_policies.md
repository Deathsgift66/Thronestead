# Alliance Tax Policies

This table defines how much tax an alliance charges on each resource for its members. It stores the current percentage rates used when calculating tax on any resource flow.

## Columns
- `alliance_id` – The alliance this policy applies to.
- `resource_type` – The resource being taxed.
- `tax_rate_percent` – Percentage of the resource taken as tax (e.g. `5.00` = 5%).
- `is_active` – Indicates if the policy is in effect.
- `updated_at` – Timestamp of the last change.
- `updated_by` – User ID of the officer or admin who updated the policy.

## Usage
1. When a player earns resources while in an alliance, look up the active tax rate from this table and deduct the appropriate amount.
2. Deducted tax is deposited into the `alliance_vault` and should be logged in `alliance_tax_collections` (not yet implemented here).
3. Officers may update tax percentages, which updates this table.
