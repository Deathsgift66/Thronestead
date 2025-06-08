# Kingdom Treaties

The `kingdom_treaties` table stores diplomatic agreements between two player kingdoms.
A row represents a single treaty proposal or active pact.

## Table Structure

| Column | Meaning / Usage |
| --- | --- |
| `treaty_id` | Unique treaty ID. Primary key. |
| `kingdom_id` | The player kingdom initiating the treaty. |
| `treaty_type` | Type of treaty (`Non-Aggression Pact`, `Defense Pact`, etc.). |
| `partner_kingdom_id` | The other kingdom in the treaty. |
| `status` | `proposed`, `active` or `cancelled`. |
| `signed_at` | Timestamp when activated or cancelled. |

## Usage

### Proposing a treaty
```sql
INSERT INTO public.kingdom_treaties (kingdom_id, partner_kingdom_id, treaty_type, status)
VALUES (?, ?, 'Non-Aggression Pact', 'proposed');
```

### Accepting a proposal
```sql
UPDATE public.kingdom_treaties
SET status = 'active', signed_at = now()
WHERE treaty_id = ?;
```

### Cancelling a treaty
```sql
UPDATE public.kingdom_treaties
SET status = 'cancelled', signed_at = now()
WHERE treaty_id = ?;
```

### Displaying on the diplomacy page
```sql
-- Active treaties
SELECT * FROM public.kingdom_treaties
WHERE (kingdom_id = ? OR partner_kingdom_id = ?) AND status = 'active';

-- Incoming proposals
SELECT * FROM public.kingdom_treaties
WHERE partner_kingdom_id = ? AND status = 'proposed';

-- Outgoing proposals
SELECT * FROM public.kingdom_treaties
WHERE kingdom_id = ? AND status = 'proposed';
```

Keep rows for history by marking them `cancelled` instead of deleting.
Avoid duplicate active treaties of the same type between the same pair of kingdoms.

