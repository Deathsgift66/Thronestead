# VIP Status System

The `kingdom_vip_status` table tracks VIP tiers for each player.

| Column     | Purpose                                |
|------------|----------------------------------------|
| user_id    | Player identifier (FK `users.user_id`) |
| vip_level  | Numeric VIP tier (0 = none)            |
| expires_at | Expiration timestamp (null for lifetime) |
| founder    | Boolean flag for lifetime VIP          |

## Example Usage

```sql
-- Grant VIP level 1 until July 1st 2025
INSERT INTO public.kingdom_vip_status (user_id, vip_level, expires_at)
VALUES ('uuid', 1, '2025-07-01')
ON CONFLICT (user_id)
DO UPDATE SET vip_level = EXCLUDED.vip_level, expires_at = EXCLUDED.expires_at;

-- Grant founder status
INSERT INTO public.kingdom_vip_status (user_id, vip_level, founder)
VALUES ('uuid', 2, true)
ON CONFLICT (user_id)
DO UPDATE SET vip_level = 2, founder = true, expires_at = NULL;
```

A status is active if `founder` is true or the VIP level is non-zero and
`expires_at` is in the future.
