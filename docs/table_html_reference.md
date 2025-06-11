## Postgres Table to HTML Reference

This document maps key PostgreSQL tables and their important columns to the HTML pages in **Kingmaker's Rise** where those fields are displayed, updated, or otherwise used in page logic.

### Table: `users`
**Relevant Columns**: `user_id`, `username`, `display_name`, `kingdom_name`, `profile_picture_url`, `profile_bio`, `region`, `kingdom_id`, `alliance_id`, `alliance_role`, `is_admin`, `setup_complete`
**Used In**:
- `login.html`: Supabase auth login to read/write `users`
- `signup.html`: new rows inserted (username, email)
- `account_settings.html`: update profile fields (display name, bio, avatar)
- `profile.html`: display avatar, username, kingdom name, motto
- `alliance_home.html`: query `alliance_id` to load alliance info
- `overview.html`: fetch `kingdom_id` to load resources
- `projects.html`, `resources.html`, `train_troops.html`, `village_master.html`: fetch `kingdom_id` for gameplay features

---

### Table: `kingdoms`
**Relevant Columns**: `kingdom_id`, `user_id`, `kingdom_name`, `region`, `prestige_score`, `economy_score`, `military_score`, `diplomacy_score`, `alliance_id`, `status`, `created_at`
**Used In**:
- `play.html`: creation during onboarding
- `overview.html`: display region info
- `profile.html`: fetch kingdom details for player profile
- `leaderboard.html`: sort kingdoms by prestige score
- `wars.html`: show attacker/defender kingdom names

---

### Table: `kingdom_resources`
**Relevant Columns**: `kingdom_id`, `wood`, `stone`, `iron_ore`, `gold`, `food`, `gems`, `coal`, `livestock`, etc.
**Used In**:
- `overview.html`: summary of current resources
- `resources.html`: detailed resource table and simulators
- `projects.html`: check costs when starting player projects
- `train_troops.html`: calculate training costs
- `play.html`: initial row created when a kingdom is formed

---

### Table: `kingdom_troops`
**Relevant Columns**: `kingdom_id`, `unit_type`, `unit_level`, `quantity`, `in_training`, `wounded`, `unit_xp`, `active_modifiers`
**Used In**:
- `train_troops.html`: queue training and show wounded/healthy counts
- `kingdom_military.html`: troop roster display (via `kingdom_troop_slots`)
- `battle_live.html` / `battle_resolution.html`: compute battle stats
- `overview.html`: show total troop count summary

---

### Table: `kingdom_troop_slots`
**Relevant Columns**: `kingdom_id`, `base_slots`, `slots_from_buildings`, `slots_from_tech`, `slots_from_projects`, `slots_from_events`, `used_slots`
**Used In**:
- `overview.html`: display available vs used troop slots
- `train_troops.html`: enforce slot limits for training queue

---

### Table: `projects_player`
**Relevant Columns**: `kingdom_id`, `project_code`, `power_score`, `starts_at`, `ends_at`
**Used In**:
- `projects.html`: list active player projects and countdown timers
- `overview.html`: show active project effects via progression API

### Table: `project_player_catalogue`
**Relevant Columns**: `project_code`, `name`, `description`, `category`, `cost`, `modifiers`, `build_time_seconds`, `project_duration_seconds`, `requires_kingdom_level`, `is_active`
**Used In**:
- `projects.html`: display available projects and requirements

---

### Table: `alliance_members`
**Relevant Columns**: `user_id`, `username`, `rank`, `contribution`, `status`, `crest`
**Used In**:
- `alliance_home.html`: roster display and contributor list
- `alliance_members.html`: sortable member roster with management controls

### Table: `alliances`
**Relevant Columns**: `alliance_id`, `name`, `leader`, `status`, `motd`, `banner`, `emblem_url`, `military_score`, `economy_score`, `diplomacy_score`, `wars_count`, `treaties_count`, `projects_active`
**Used In**:
- `alliance_home.html`: show main alliance details
- `alliance_treaties.html`, `treaty_web.html`: load alliance network info
- `alliance_wars.html`: list wars belonging to the alliance

### Table: `alliance_vault`
**Relevant Columns**: `alliance_id`, `wood`, `stone`, `gold`, `food`, `fortification_level`, `army_count`, `created_at`
**Used In**:
- `alliance_home.html`: show shared resource vault
- `alliance_vault.html`: deposit/withdraw resources and view transaction history

### Table: `alliance_achievements`
**Relevant Columns**: `alliance_id`, `achievement_code`, `awarded_at`
**Used In**:
- `alliance_home.html`: list earned achievements with descriptions via joined catalogue

---

### Table: `quest_alliance_catalogue`
**Relevant Columns**: `quest_code`, `name`, `description`, `objectives`, `rewards`, `is_repeatable`
**Used In**:
- `alliance_quests.html`: display available alliance quests

### Table: `quest_alliance_tracking`
**Relevant Columns**: `alliance_id`, `quest_code`, `progress`, `completed`, `started_at`, `expires_at`
**Used In**:
- `alliance_quests.html`: show active quest progress bars

### Table: `quest_alliance_contributions`
**Relevant Columns**: `contribution_id`, `alliance_id`, `player_name`, `resource_type`, `amount`, `timestamp`, `quest_code`, `user_id`
**Used In**:
- `alliance_quests.html`: track contribution logs and leaderboards

---

### Table: `wars`
**Relevant Columns**: `war_id`, `attacker_kingdom_id`, `defender_kingdom_id`, `attacker_name`, `defender_name`, `status`, `start_date`, `end_date`, `attacker_score`, `defender_score`, `war_reason`
**Used In**:
- `wars.html`: list active wars and allow declarations via modal
- `battle_live.html`, `battle_replay.html`, `battle_resolution.html`: display war results and scores
- `alliance_wars.html`: show alliance-specific war history

### Table: `training_catalog`
**Relevant Columns**: `unit_id`, `unit_name`, `tier`, `training_time`, `cost_gold`, `cost_food`, `cost_iron`, `cost_wood`, `cost_horses`
**Used In**:
- `train_troops.html`: troop catalogue listing and cost calculations

### Table: `training_queue`
**Relevant Columns**: `queue_id`, `kingdom_id`, `unit_id`, `unit_name`, `quantity`, `training_ends_at`
**Used In**:
- `train_troops.html`: display current training queue

### Table: `training_history`
**Relevant Columns**: `history_id`, `kingdom_id`, `unit_name`, `quantity`, `completed_at`, `source`, `xp_awarded`
**Used In**:
- `train_troops.html`: recent training history list

### Table: `trade_logs`
**Relevant Columns**: `trade_id`, `sender_id`, `receiver_id`, `resource_type`, `amount`, `timestamp`, `status`
**Used In**:
- `trade_logs.html`: trade history tables

### Table: `audit_log`
**Relevant Columns**: `log_id`, `user_id`, `action`, `details`, `created_at`
**Used In**:
- `admin_dashboard.html`: admin panel to review actions
- `profile.html`: recent actions feed for the current player

### Table: `player_messages`
**Relevant Columns**: `message_id`, `sender_id`, `receiver_id`, `subject`, `body`, `sent_at`, `is_read`
**Used In**:
- `messages.html`: inbox listing and message reading
- `message.html`: display a single message
- `compose.html`: send new messages

### Table: `village_buildings`
**Relevant Columns**: `village_id`, `building_code`, `level`, `last_updated`
**Used In**:
- `village.html`: show and upgrade individual village buildings
- `village_master.html`: aggregated building levels across villages

### Table: `village_modifiers`
**Relevant Columns**: `village_id`, `modifier_code`, `value`, `expires_at`
**Used In**:
- `village.html`: display active modifiers affecting the village

### Table: `villages`
**Relevant Columns**: `village_id`, `kingdom_id`, `village_name`, `region`, `population`, `created_at`
**Used In**:
- `village_master.html`: list all villages belonging to a kingdom
- `village.html`: render specific village details

### Table: `region_catalogue`
**Relevant Columns**: `region_code`, `region_name`, `description`, `resource_bonus`, `troop_bonus`
**Used In**:
- `play.html`: region selection during kingdom creation
- `overview.html`: convert region code to display name

---

This reference covers the primary gameplay-related tables. Many additional tables exist (titles, spy missions, policies, seasonal effects, etc.) that follow a similar pattern: JavaScript files load data via Supabase or API routes and HTML pages render that data using dynamic templates.
