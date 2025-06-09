# public.users — Player Profiles

This table links Supabase auth IDs to in-game profiles and stores all account level metadata.

## Table Structure

| Column | Purpose |
| --- | --- |
| `user_id` | UUID from Supabase auth. Primary key. |
| `username` | Unique in-game handle. |
| `display_name` | Optional display name override. |
| `kingdom_name` | Player's official kingdom name. |
| `email` | Login email address. |
| `profile_bio` | Optional profile text. |
| `profile_picture_url` | Avatar image URL. |
| `region` | Starting region code. |
| `kingdom_id` | FK to `kingdoms.kingdom_id`. |
| `alliance_id` | Alliance membership FK. |
| `alliance_role` | Role within the alliance. |
| `active_policy` | Selected national policy ID. |
| `active_laws` | Array of active law IDs. |
| `is_admin` | Grants admin access if true. |
| `is_banned` | Blocks login when true. |
| `is_deleted` | Soft delete flag. |
| `setup_complete` | Whether onboarding finished. |
| `sign_up_date` | Date part of signup timestamp. |
| `sign_up_time` | Time part of signup timestamp. |
| `created_at` | Row creation timestamp. |
| `updated_at` | Last profile update. |

## Usage
- Always treat `user_id` as the canonical identifier for joins.
- Use `setup_complete` to gate access to core game features.
- Do not hard delete rows; toggle `is_deleted` instead.
