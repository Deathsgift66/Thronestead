# Final Schema Documentation
**Schema Version: 6.11.25**


This file lists the complete SQL schema used by the application.

```sql
CREATE TABLE public.alliance_achievement_catalogue (
  achievement_code text NOT NULL,
  name text NOT NULL,
  description text,
  category text DEFAULT 'general'::text,
  points_reward integer DEFAULT 0,
  badge_icon_url text,
  is_hidden boolean DEFAULT false,
  is_repeatable boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT alliance_achievement_catalogue_pkey PRIMARY KEY (achievement_code)
);

CREATE TABLE public.alliance_achievements (
  alliance_id integer,
  achievement_code text,
  awarded_at timestamp with time zone DEFAULT now(),
  CONSTRAINT alliance_achievements_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliance_activity_log (
  log_id integer NOT NULL DEFAULT nextval('alliance_activity_log_log_id_seq'::regclass),
  alliance_id integer,
  user_id uuid,
  action text,
  description text,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT alliance_activity_log_pkey PRIMARY KEY (log_id),
  CONSTRAINT alliance_activity_log_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_activity_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.alliance_grants (
  grant_id integer NOT NULL DEFAULT nextval('alliance_grants_grant_id_seq'::regclass),
  alliance_id integer NOT NULL,
  recipient_user_id uuid NOT NULL,
  resource_type text NOT NULL,
  amount bigint NOT NULL DEFAULT 0,
  granted_at timestamp with time zone DEFAULT now(),
  reason text,
  CONSTRAINT alliance_grants_pkey PRIMARY KEY (grant_id),
  CONSTRAINT alliance_grants_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_grants_recipient_user_id_fkey FOREIGN KEY (recipient_user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.alliance_loans (
  loan_id integer NOT NULL DEFAULT nextval('alliance_loans_loan_id_seq'::regclass),
  alliance_id integer NOT NULL,
  borrower_user_id uuid NOT NULL,
  resource_type text NOT NULL,
  amount bigint NOT NULL DEFAULT 0,
  amount_repaid bigint NOT NULL DEFAULT 0,
  interest_rate numeric DEFAULT 0.05,
  due_date timestamp with time zone,
  status text DEFAULT 'active'::text CHECK (status = ANY (ARRAY['active'::text, 'repaid'::text, 'defaulted'::text])),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  default_penalty_rate numeric DEFAULT 0.10,
  is_tax_active boolean DEFAULT false,
  tax_started_at timestamp with time zone,
  CONSTRAINT alliance_loans_pkey PRIMARY KEY (loan_id),
  CONSTRAINT alliance_loans_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_loans_borrower_user_id_fkey FOREIGN KEY (borrower_user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.alliance_members (
  alliance_id integer NOT NULL,
  user_id uuid NOT NULL,
  username text,
  rank text,
  contribution integer DEFAULT 0,
  status text,
  crest text,
  role_id integer,
  CONSTRAINT alliance_members_pkey PRIMARY KEY (alliance_id, user_id),
  CONSTRAINT alliance_members_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_members_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.alliance_roles(role_id)
);

CREATE TABLE public.alliance_policies (
  alliance_id integer NOT NULL,
  policy_id integer NOT NULL,
  applied_at timestamp without time zone DEFAULT now(),
  is_active boolean DEFAULT true,
  CONSTRAINT alliance_policies_pkey PRIMARY KEY (alliance_id, policy_id),
  CONSTRAINT alliance_policies_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_policies_policy_id_fkey FOREIGN KEY (policy_id) REFERENCES public.policies_laws_catalogue(id)
);

CREATE TABLE public.alliance_roles (
  role_id integer NOT NULL DEFAULT nextval('alliance_roles_role_id_seq'::regclass),
  alliance_id integer,
  role_name text NOT NULL,
  permissions jsonb DEFAULT '{}'::jsonb,
  is_default boolean DEFAULT false,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT alliance_roles_pkey PRIMARY KEY (role_id),
  CONSTRAINT alliance_roles_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliance_tax_collections (
  collection_id bigint NOT NULL DEFAULT nextval('alliance_tax_collections_collection_id_seq'::regclass),
  alliance_id integer NOT NULL,
  user_id uuid NOT NULL,
  resource_type text NOT NULL,
  amount_collected bigint DEFAULT 0,
  collected_at timestamp with time zone DEFAULT now(),
  source text,
  notes text,
  CONSTRAINT alliance_tax_collections_pkey PRIMARY KEY (collection_id),
  CONSTRAINT alliance_tax_collections_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_tax_collections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.alliance_tax_policies (
  alliance_id integer NOT NULL,
  resource_type text NOT NULL,
  tax_rate_percent numeric DEFAULT 0,
  is_active boolean DEFAULT true,
  updated_at timestamp with time zone DEFAULT now(),
  updated_by uuid,
  CONSTRAINT alliance_tax_policies_pkey PRIMARY KEY (alliance_id, resource_type),
  CONSTRAINT alliance_tax_policies_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_tax_policies_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.alliance_treaties (
  treaty_id integer NOT NULL DEFAULT nextval('alliance_treaties_treaty_id_seq'::regclass),
  alliance_id integer,
  treaty_type text,
  partner_alliance_id integer,
  status text CHECK (status = ANY (ARRAY['proposed'::text, 'active'::text, 'cancelled'::text])),
  signed_at timestamp with time zone DEFAULT now(),
  CONSTRAINT alliance_treaties_pkey PRIMARY KEY (treaty_id),
  CONSTRAINT alliance_treaties_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_treaties_partner_alliance_id_fkey FOREIGN KEY (partner_alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliance_vault (
  alliance_id integer NOT NULL,
  wood bigint DEFAULT 0,
  stone bigint DEFAULT 0,
  iron_ore bigint DEFAULT 0,
  gold bigint DEFAULT 0,
  gems bigint DEFAULT 0,
  food bigint DEFAULT 0,
  coal bigint DEFAULT 0,
  livestock bigint DEFAULT 0,
  clay bigint DEFAULT 0,
  flax bigint DEFAULT 0,
  tools bigint DEFAULT 0,
  wood_planks bigint DEFAULT 0,
  refined_stone bigint DEFAULT 0,
  iron_ingots bigint DEFAULT 0,
  charcoal bigint DEFAULT 0,
  leather bigint DEFAULT 0,
  arrows bigint DEFAULT 0,
  swords bigint DEFAULT 0,
  axes bigint DEFAULT 0,
  shields bigint DEFAULT 0,
  armour bigint DEFAULT 0,
  wagon bigint DEFAULT 0,
  siege_weapons bigint DEFAULT 0,
  jewelry bigint DEFAULT 0,
  spear bigint DEFAULT 0,
  horses bigint DEFAULT 0,
  pitchforks bigint DEFAULT 0,
  fortification_level integer DEFAULT 0,
  army_count integer DEFAULT 0,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT alliance_vault_pkey PRIMARY KEY (alliance_id),
  CONSTRAINT alliance_vault_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliance_vault_transaction_log (
  transaction_id bigint NOT NULL DEFAULT nextval('alliance_vault_transaction_log_transaction_id_seq'::regclass),
  alliance_id integer NOT NULL,
  user_id uuid,
  action text CHECK (action = ANY (ARRAY['deposit'::text, 'withdraw'::text, 'transfer'::text, 'trade'::text])),
  resource_type text NOT NULL,
  amount bigint NOT NULL,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT alliance_vault_transaction_log_pkey PRIMARY KEY (transaction_id),
  CONSTRAINT alliance_vault_transaction_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id),
  CONSTRAINT alliance_vault_transaction_log_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliance_war_combat_logs (
  combat_id integer NOT NULL DEFAULT nextval('alliance_war_combat_logs_combat_id_seq'::regclass),
  alliance_war_id integer,
  tick_number integer NOT NULL,
  event_type text NOT NULL,
  attacker_unit_id integer,
  defender_unit_id integer,
  position_x integer,
  position_y integer,
  damage_dealt integer DEFAULT 0,
  morale_shift double precision DEFAULT 0,
  notes text,
  timestamp timestamp without time zone DEFAULT now(),
  CONSTRAINT alliance_war_combat_logs_pkey PRIMARY KEY (combat_id),
  CONSTRAINT alliance_war_combat_logs_alliance_war_id_fkey FOREIGN KEY (alliance_war_id) REFERENCES public.alliance_wars(alliance_war_id)
);

CREATE TABLE public.alliance_war_participants (
  alliance_war_id integer NOT NULL,
  kingdom_id integer NOT NULL,
  role text CHECK (role = ANY (ARRAY['attacker'::text, 'defender'::text])),
  CONSTRAINT alliance_war_participants_pkey PRIMARY KEY (alliance_war_id, kingdom_id),
  CONSTRAINT alliance_war_participants_alliance_war_id_fkey FOREIGN KEY (alliance_war_id) REFERENCES public.alliance_wars(alliance_war_id),
  CONSTRAINT alliance_war_participants_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.alliance_war_preplans (
  preplan_id integer NOT NULL DEFAULT nextval('alliance_war_preplans_preplan_id_seq'::regclass),
  alliance_war_id integer,
  kingdom_id integer,
  preplan_jsonb jsonb NOT NULL,
  last_updated timestamp without time zone DEFAULT now(),
  CONSTRAINT alliance_war_preplans_pkey PRIMARY KEY (preplan_id),
  CONSTRAINT alliance_war_preplans_alliance_war_id_fkey FOREIGN KEY (alliance_war_id) REFERENCES public.alliance_wars(alliance_war_id),
  CONSTRAINT alliance_war_preplans_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.alliance_war_scores (
  alliance_war_id integer NOT NULL,
  attacker_score integer DEFAULT 0,
  defender_score integer DEFAULT 0,
  attacker_kills integer DEFAULT 0,
  defender_kills integer DEFAULT 0,
  attacker_losses integer DEFAULT 0,
  defender_losses integer DEFAULT 0,
  resources_plundered integer DEFAULT 0,
  battles_participated integer DEFAULT 0,
  victor text CHECK (victor = ANY (ARRAY['attacker'::text, 'defender'::text, 'draw'::text])),
  last_updated timestamp without time zone DEFAULT now(),
  CONSTRAINT alliance_war_scores_pkey PRIMARY KEY (alliance_war_id),
  CONSTRAINT alliance_war_scores_alliance_war_id_fkey FOREIGN KEY (alliance_war_id) REFERENCES public.alliance_wars(alliance_war_id)
);

CREATE TABLE public.alliance_wars (
  alliance_war_id integer NOT NULL DEFAULT nextval('alliance_wars_alliance_war_id_seq'::regclass),
  attacker_alliance_id integer,
  defender_alliance_id integer,
  phase USER-DEFINED DEFAULT 'alert'::war_phase,
  castle_hp integer DEFAULT 10000,
  battle_tick integer DEFAULT 0,
  war_status USER-DEFINED DEFAULT 'active'::war_status,
  start_date timestamp without time zone DEFAULT now(),
  end_date timestamp without time zone,
  CONSTRAINT alliance_wars_pkey PRIMARY KEY (alliance_war_id),
  CONSTRAINT alliance_wars_attacker_alliance_id_fkey FOREIGN KEY (attacker_alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_wars_defender_alliance_id_fkey FOREIGN KEY (defender_alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliances (
  alliance_id integer NOT NULL DEFAULT nextval('alliances_alliance_id_seq'::regclass),
  name text NOT NULL,
  leader text,
  status text,
  region text,
  level integer DEFAULT 1,
  motd text,
  banner text,
  created_at timestamp with time zone DEFAULT now(),
  military_score integer DEFAULT 0,
  economy_score integer DEFAULT 0,
  diplomacy_score integer DEFAULT 0,
  wars_count integer DEFAULT 0,
  treaties_count integer DEFAULT 0,
  projects_active integer DEFAULT 0,
  emblem_url text,
  CONSTRAINT alliances_pkey PRIMARY KEY (alliance_id)
);

CREATE TABLE public.audit_log (
  log_id integer NOT NULL DEFAULT nextval('audit_log_log_id_seq'::regclass),
  user_id uuid,
  action text,
  details text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT audit_log_pkey PRIMARY KEY (log_id)
);

CREATE TABLE public.battle_resolution_logs (
  resolution_id integer NOT NULL DEFAULT nextval('battle_resolution_logs_resolution_id_seq'::regclass),
  battle_type text NOT NULL CHECK (battle_type = ANY (ARRAY['kingdom'::text, 'alliance'::text])),
  war_id integer,
  alliance_war_id integer,
  winner_side text NOT NULL CHECK (winner_side = ANY (ARRAY['attacker'::text, 'defender'::text, 'draw'::text])),
  total_ticks integer DEFAULT 0,
  attacker_casualties integer DEFAULT 0,
  defender_casualties integer DEFAULT 0,
  loot_summary jsonb DEFAULT '{}'::jsonb,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT battle_resolution_logs_pkey PRIMARY KEY (resolution_id),
  CONSTRAINT battle_resolution_logs_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id),
  CONSTRAINT battle_resolution_logs_alliance_war_id_fkey FOREIGN KEY (alliance_war_id) REFERENCES public.alliance_wars(alliance_war_id)
);

CREATE TABLE public.black_market_listings (
  listing_id integer NOT NULL DEFAULT nextval('black_market_listings_listing_id_seq'::regclass),
  seller_id uuid,
  item text,
  price numeric,
  quantity integer,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT black_market_listings_pkey PRIMARY KEY (listing_id)
);

CREATE TABLE public.building_catalogue (
  building_id integer NOT NULL DEFAULT nextval('building_catalogue_building_id_seq'::regclass),
  building_name text NOT NULL,
  description text,
  production_type text,
  production_rate integer,
  upkeep integer,
  build_cost jsonb,
  modifiers jsonb DEFAULT '{}'::jsonb,
  category text,
  build_time_seconds integer DEFAULT 3600,
  prerequisites jsonb DEFAULT '{}'::jsonb,
  max_level integer DEFAULT 10,
  special_effects jsonb DEFAULT '{}'::jsonb,
  is_unique boolean DEFAULT false,
  is_repeatable boolean DEFAULT true,
  unlock_at_level integer DEFAULT 1,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT building_catalogue_pkey PRIMARY KEY (building_id)
);

CREATE TABLE public.combat_logs (
  combat_id integer NOT NULL DEFAULT nextval('combat_logs_combat_id_seq'::regclass),
  war_id integer,
  tick_number integer,
  event_type text,
  attacker_unit_id integer,
  defender_unit_id integer,
  position_x integer,
  position_y integer,
  damage_dealt integer,
  morale_shift double precision,
  notes text,
  timestamp timestamp with time zone DEFAULT now(),
  CONSTRAINT combat_logs_pkey PRIMARY KEY (combat_id),
  CONSTRAINT combat_logs_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id)
);
CREATE INDEX combat_logs_war_id_idx ON public.combat_logs(war_id);

CREATE TABLE public.game_settings (
  setting_key text NOT NULL,
  setting_value jsonb,
  setting_type text,
  description text,
  default_value jsonb,
  is_active boolean DEFAULT true,
  last_updated timestamp with time zone DEFAULT now(),
  updated_by uuid,
  CONSTRAINT game_settings_pkey PRIMARY KEY (setting_key)
);

CREATE TABLE public.global_events (
  event_id integer NOT NULL DEFAULT nextval('global_events_event_id_seq'::regclass),
  name text,
  description text,
  start_time timestamp without time zone,
  end_time timestamp without time zone,
  impact jsonb DEFAULT '{}'::jsonb,
  is_active boolean DEFAULT false,
  CONSTRAINT global_events_pkey PRIMARY KEY (event_id)
);

CREATE TABLE public.kingdom_achievement_catalogue (
  achievement_code text NOT NULL,
  name text NOT NULL,
  description text,
  category text,
  reward jsonb DEFAULT '{}'::jsonb,
  points integer DEFAULT 0,
  is_hidden boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_achievement_catalogue_pkey PRIMARY KEY (achievement_code)
);

CREATE TABLE public.kingdom_achievements (
  kingdom_id integer,
  achievement_code text,
  awarded_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_achievements_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_history_log (
  log_id integer NOT NULL DEFAULT nextval('kingdom_history_log_log_id_seq'::regclass),
  kingdom_id integer,
  event_type text,
  event_details text,
  event_date timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_history_log_pkey PRIMARY KEY (log_id),
  CONSTRAINT kingdom_history_log_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_religion (
  kingdom_id integer,
  religion_name text,
  faith_level integer DEFAULT 1,
  faith_points integer DEFAULT 0,
  blessings jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT kingdom_religion_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_research_tracking (
  kingdom_id integer NOT NULL,
  tech_code text NOT NULL,
  status text CHECK (status = ANY (ARRAY['active'::text, 'completed'::text, 'locked'::text])),
  progress integer DEFAULT 0,
  ends_at timestamp with time zone,
  CONSTRAINT kingdom_research_tracking_pkey PRIMARY KEY (kingdom_id, tech_code),
  CONSTRAINT kingdom_research_tracking_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT kingdom_research_tracking_tech_code_fkey FOREIGN KEY (tech_code) REFERENCES public.tech_catalogue(tech_code)
);

CREATE TABLE public.kingdom_resources (
  kingdom_id integer NOT NULL,
  wood bigint DEFAULT 0,
  stone bigint DEFAULT 0,
  iron_ore bigint DEFAULT 0,
  gold bigint DEFAULT 0,
  gems bigint DEFAULT 0,
  food bigint DEFAULT 0,
  coal bigint DEFAULT 0,
  livestock bigint DEFAULT 0,
  clay bigint DEFAULT 0,
  flax bigint DEFAULT 0,
  tools bigint DEFAULT 0,
  wood_planks bigint DEFAULT 0,
  refined_stone bigint DEFAULT 0,
  iron_ingots bigint DEFAULT 0,
  charcoal bigint DEFAULT 0,
  leather bigint DEFAULT 0,
  arrows bigint DEFAULT 0,
  swords bigint DEFAULT 0,
  axes bigint DEFAULT 0,
  shields bigint DEFAULT 0,
  armour bigint DEFAULT 0,
  wagon bigint DEFAULT 0,
  siege_weapons bigint DEFAULT 0,
  jewelry bigint DEFAULT 0,
  spear bigint DEFAULT 0,
  horses bigint DEFAULT 0,
  pitchforks bigint DEFAULT 0,
  CONSTRAINT kingdom_resources_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdom_resources_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_spies (
  kingdom_id integer NOT NULL,
  spy_level integer DEFAULT 1,
  spy_count integer DEFAULT 0,
  max_spy_capacity integer DEFAULT 10,
  spy_xp integer DEFAULT 0,
  spy_upkeep_gold integer DEFAULT 0,
  last_mission_at timestamp with time zone,
  cooldown_seconds integer DEFAULT 0,
  spies_lost integer DEFAULT 0,
  missions_attempted integer DEFAULT 0,
  missions_successful integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_spies_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdom_spies_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_titles (
  kingdom_id integer,
  title text,
  awarded_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_titles_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_treaties (
  treaty_id integer NOT NULL DEFAULT nextval('kingdom_treaties_treaty_id_seq'::regclass),
  kingdom_id integer,
  treaty_type text,
  partner_kingdom_id integer,
  status text CHECK (status = ANY (ARRAY['proposed'::text, 'active'::text, 'cancelled'::text])),
  signed_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_treaties_pkey PRIMARY KEY (treaty_id),
  CONSTRAINT kingdom_treaties_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT kingdom_treaties_partner_kingdom_id_fkey FOREIGN KEY (partner_kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_troop_slots (
  kingdom_id integer NOT NULL,
  base_slots integer DEFAULT 20,
  used_slots integer DEFAULT 0,
  morale integer DEFAULT 100,
  slots_from_buildings integer DEFAULT 0,
  slots_from_tech integer DEFAULT 0,
  slots_from_projects integer DEFAULT 0,
  slots_from_events integer DEFAULT 0,
  morale_bonus_buildings integer DEFAULT 0,
  morale_bonus_tech integer DEFAULT 0,
  morale_bonus_events integer DEFAULT 0,
  last_morale_update timestamp with time zone DEFAULT now(),
  morale_cooldown_seconds integer DEFAULT 0,
  last_in_combat_at timestamp with time zone,
  currently_in_combat boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_troop_slots_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdom_troop_slots_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_troops (
  kingdom_id integer NOT NULL,
  unit_type text NOT NULL,
  quantity integer DEFAULT 0,
  last_updated timestamp without time zone DEFAULT now(),
  in_training integer DEFAULT 0,
  wounded integer DEFAULT 0,
  unit_xp integer DEFAULT 0,
  unit_level integer NOT NULL DEFAULT 1,
  active_modifiers jsonb DEFAULT '{}'::jsonb,
  last_modified_by uuid,
  last_combat_at timestamp with time zone,
  last_morale integer DEFAULT 100,
  CONSTRAINT kingdom_troops_pkey PRIMARY KEY (kingdom_id, unit_type, unit_level),
  CONSTRAINT kingdom_troops_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT kingdom_troops_unit_type_fkey FOREIGN KEY (unit_type) REFERENCES public.unit_stats(unit_type)
);

CREATE TABLE public.kingdom_villages (
  village_id integer NOT NULL DEFAULT nextval('kingdom_villages_village_id_seq'::regclass),
  kingdom_id integer,
  village_name text NOT NULL,
  village_type text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_villages_pkey PRIMARY KEY (village_id),
  CONSTRAINT kingdom_villages_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_vip_status (
  user_id uuid NOT NULL,
  vip_level integer DEFAULT 0,
  expires_at timestamp with time zone,
  founder boolean DEFAULT false,
  CONSTRAINT kingdom_vip_status_pkey PRIMARY KEY (user_id)
);

CREATE TABLE public.kingdoms (
  kingdom_id integer NOT NULL DEFAULT nextval('kingdoms_kingdom_id_seq'::regclass),
  user_id uuid UNIQUE,
  kingdom_name text NOT NULL,
  region text,
  created_at timestamp with time zone DEFAULT now(),
  prestige_score integer DEFAULT 0,
  avatar_url text,
  status text DEFAULT 'active'::text,
  description text,
  motto text,
  ruler_name text,
  alliance_id integer,
  alliance_role text,
  tech_level integer DEFAULT 1,
  economy_score integer DEFAULT 0,
  military_score integer DEFAULT 0,
  diplomacy_score integer DEFAULT 0,
  last_login_at timestamp with time zone,
  last_updated timestamp with time zone DEFAULT now(),
  is_npc boolean DEFAULT false,
  customizations jsonb DEFAULT '{}'::jsonb,
  is_on_vacation boolean DEFAULT false,
  vacation_started_at timestamp with time zone,
  vacation_expires_at timestamp with time zone,
  CONSTRAINT kingdoms_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdoms_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.notifications (
  notification_id integer NOT NULL DEFAULT nextval('notifications_notification_id_seq'::regclass),
  user_id uuid,
  title text,
  message text,
  category text,
  priority text,
  link_action text,
  created_at timestamp with time zone DEFAULT now(),
  is_read boolean DEFAULT false,
  expires_at timestamp with time zone,
  source_system text,
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT notifications_pkey PRIMARY KEY (notification_id),
  CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.player_messages (
  message_id integer NOT NULL DEFAULT nextval('player_messages_message_id_seq'::regclass),
  user_id uuid,
  recipient_id uuid,
  message text,
  sent_at timestamp with time zone DEFAULT now(),
  is_read boolean DEFAULT false,
  CONSTRAINT player_messages_pkey PRIMARY KEY (message_id)
);

CREATE TABLE public.policies_laws_catalogue (
  id integer NOT NULL DEFAULT nextval('policies_laws_catalogue_id_seq'::regclass),
  type text CHECK (type = ANY (ARRAY['policy'::text, 'law'::text])),
  name text NOT NULL,
  description text,
  effect_summary text,
  CONSTRAINT policies_laws_catalogue_pkey PRIMARY KEY (id)
);

CREATE TABLE public.project_alliance_catalogue (
  project_id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  project_key text NOT NULL,
  project_name text NOT NULL,
  description text,
  category text,
  effect_summary text,
  is_repeatable boolean DEFAULT false,
  required_tech ARRAY,
  prerequisites ARRAY,
  unlocks ARRAY,
  resource_costs jsonb DEFAULT '{}'::jsonb,
  build_time_seconds integer DEFAULT 3600,
  project_duration_seconds integer,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  user_id uuid,
  modifiers jsonb DEFAULT '{}'::jsonb,
  requires_alliance_level integer DEFAULT 1,
  is_active boolean DEFAULT true,
  max_active_instances integer,
  expires_at timestamp with time zone,
  CONSTRAINT project_alliance_catalogue_pkey PRIMARY KEY (project_id),
  CONSTRAINT project_alliance_catalogue_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.project_player_catalogue (
  project_code text NOT NULL,
  name text NOT NULL,
  description text,
  power_score integer DEFAULT 0,
  cost jsonb,
  modifiers jsonb DEFAULT '{}'::jsonb,
  category text,
  is_repeatable boolean DEFAULT true,
  prerequisites ARRAY,
  unlocks ARRAY,
  build_time_seconds integer DEFAULT 3600,
  project_duration_seconds integer,
  requires_kingdom_level integer DEFAULT 1,
  is_active boolean DEFAULT true,
  max_active_instances integer,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  user_id uuid,
  required_tech ARRAY,
  requires_region text,
  effect_summary text,
  expires_at timestamp with time zone,
  last_modified_by uuid,
  CONSTRAINT project_player_catalogue_pkey PRIMARY KEY (project_code),
  CONSTRAINT project_player_catalogue_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id),
  CONSTRAINT project_player_catalogue_last_modified_by_fkey FOREIGN KEY (last_modified_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.projects_alliance (
  project_id integer NOT NULL DEFAULT nextval('projects_alliance_project_id_seq'::regclass),
  alliance_id integer,
  name text NOT NULL,
  progress integer DEFAULT 0,
  modifiers jsonb DEFAULT '{}'::jsonb,
  project_key text,
  start_time timestamp with time zone DEFAULT now(),
  end_time timestamp with time zone,
  is_active boolean DEFAULT true,
  build_state text DEFAULT 'queued'::text CHECK (build_state = ANY (ARRAY['queued'::text, 'building'::text, 'completed'::text, 'expired'::text])),
  built_by uuid,
  expires_at timestamp with time zone,
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT projects_alliance_pkey PRIMARY KEY (project_id),
  CONSTRAINT projects_alliance_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT projects_alliance_built_by_fkey FOREIGN KEY (built_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.projects_alliance_in_progress (
  progress_id integer NOT NULL DEFAULT nextval('projects_alliance_in_progress_progress_id_seq'::regclass),
  alliance_id integer,
  project_key text,
  progress integer DEFAULT 0,
  started_at timestamp without time zone DEFAULT now(),
  expected_end timestamp without time zone,
  status text DEFAULT 'building'::text CHECK (status = ANY (ARRAY['building'::text, 'paused'::text, 'completed'::text])),
  built_by uuid,
  CONSTRAINT projects_alliance_in_progress_pkey PRIMARY KEY (progress_id),
  CONSTRAINT projects_alliance_in_progress_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT projects_alliance_in_progress_built_by_fkey FOREIGN KEY (built_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.projects_player (
  project_id integer NOT NULL DEFAULT nextval('projects_player_project_id_seq'::regclass),
  kingdom_id integer,
  project_code text,
  power_score integer DEFAULT 0,
  starts_at timestamp with time zone DEFAULT now(),
  ends_at timestamp with time zone,
  CONSTRAINT projects_player_pkey PRIMARY KEY (project_id),
  CONSTRAINT projects_player_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT projects_player_project_code_fkey FOREIGN KEY (project_code) REFERENCES public.project_player_catalogue(project_code)
);

CREATE TABLE public.quest_alliance_catalogue (
  quest_code text NOT NULL,
  name text NOT NULL,
  description text,
  duration_hours integer,
  category text,
  objectives jsonb DEFAULT '{}'::jsonb,
  rewards jsonb DEFAULT '{}'::jsonb,
  required_level integer DEFAULT 1,
  repeatable boolean DEFAULT true,
  max_attempts integer,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT quest_alliance_catalogue_pkey PRIMARY KEY (quest_code)
);

CREATE TABLE public.quest_alliance_contributions (
  contribution_id integer NOT NULL DEFAULT nextval('quest_alliance_contributions_contribution_id_seq'::regclass),
  alliance_id integer,
  player_name text,
  resource_type USER-DEFINED,
  amount integer,
  timestamp timestamp with time zone DEFAULT now(),
  quest_code text,
  user_id uuid,
  contribution_type text DEFAULT 'resource'::text,
  CONSTRAINT quest_alliance_contributions_pkey PRIMARY KEY (contribution_id),
  CONSTRAINT quest_alliance_contributions_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT quest_alliance_contributions_quest_code_fkey FOREIGN KEY (quest_code) REFERENCES public.quest_alliance_catalogue(quest_code),
  CONSTRAINT quest_alliance_contributions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.quest_alliance_tracking (
  alliance_id integer NOT NULL,
  quest_code text NOT NULL,
  status text CHECK (status = ANY (ARRAY['active'::text, 'completed'::text])),
  progress integer DEFAULT 0,
  ends_at timestamp with time zone,
  started_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  attempt_count integer DEFAULT 1,
  started_by uuid,
  CONSTRAINT quest_alliance_tracking_pkey PRIMARY KEY (alliance_id, quest_code),
  CONSTRAINT quest_alliance_tracking_started_by_fkey FOREIGN KEY (started_by) REFERENCES public.users(user_id),
  CONSTRAINT quest_alliance_tracking_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT quest_alliance_tracking_quest_code_fkey FOREIGN KEY (quest_code) REFERENCES public.quest_alliance_catalogue(quest_code)
);

CREATE TABLE public.quest_kingdom_catalogue (
  quest_code text NOT NULL,
  name text NOT NULL,
  description text,
  duration_hours integer,
  category text,
  objectives jsonb DEFAULT '{}'::jsonb,
  rewards jsonb DEFAULT '{}'::jsonb,
  required_level integer DEFAULT 1,
  repeatable boolean DEFAULT true,
  max_attempts integer,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT quest_kingdom_catalogue_pkey PRIMARY KEY (quest_code)
);

CREATE TABLE public.quest_kingdom_tracking (
  kingdom_id integer NOT NULL,
  quest_code text NOT NULL,
  status text CHECK (status = ANY (ARRAY['active'::text, 'completed'::text, 'cancelled'::text, 'expired'::text])),
  progress integer DEFAULT 0,
  ends_at timestamp with time zone,
  progress_details jsonb DEFAULT '{}'::jsonb,
  started_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  attempt_count integer DEFAULT 1,
  started_by uuid,
  CONSTRAINT quest_kingdom_tracking_pkey PRIMARY KEY (kingdom_id, quest_code),
  CONSTRAINT quest_kingdom_tracking_started_by_fkey FOREIGN KEY (started_by) REFERENCES public.users(user_id),
  CONSTRAINT quest_kingdom_tracking_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT quest_kingdom_tracking_quest_code_fkey FOREIGN KEY (quest_code) REFERENCES public.quest_kingdom_catalogue(quest_code)
);

CREATE TABLE public.region_catalogue (
  region_code text NOT NULL,
  region_name text NOT NULL,
  description text,
  resource_bonus jsonb DEFAULT '{}'::jsonb,
  troop_bonus jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT region_catalogue_pkey PRIMARY KEY (region_code)
);

CREATE TABLE public.spy_missions (
  mission_id integer NOT NULL DEFAULT nextval('spy_missions_mission_id_seq'::regclass),
  kingdom_id integer,
  mission_type text,
  target_id integer,
  status text CHECK (status = ANY (ARRAY['active'::text, 'success'::text, 'fail'::text])),
  launched_at timestamp with time zone DEFAULT now(),
  completed_at timestamp with time zone,
  CONSTRAINT spy_missions_pkey PRIMARY KEY (mission_id),
  CONSTRAINT spy_missions_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.tech_catalogue (
  tech_code text NOT NULL,
  name text NOT NULL,
  description text,
  category text,
  tier integer,
  duration_hours integer,
  encyclopedia_entry text,
  modifiers jsonb DEFAULT '{}'::jsonb,
  prerequisites ARRAY,
  required_kingdom_level integer DEFAULT 1,
  required_region text,
  is_repeatable boolean DEFAULT false,
  max_research_level integer,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT tech_catalogue_pkey PRIMARY KEY (tech_code)
);

CREATE TABLE public.terrain_map (
  terrain_id integer NOT NULL DEFAULT nextval('terrain_map_terrain_id_seq'::regclass),
  war_id integer,
  tile_map jsonb,
  generated_at timestamp with time zone DEFAULT now(),
  map_width integer,
  map_height integer,
  map_seed integer,
  map_version integer DEFAULT 1,
  generated_by uuid,
  map_name text,
  last_updated timestamp with time zone DEFAULT now(),
  map_type text DEFAULT 'battlefield'::text,
  tile_schema_version integer DEFAULT 1,
  is_active boolean DEFAULT true,
  map_source text DEFAULT 'auto-generated'::text,
  map_features jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT terrain_map_pkey PRIMARY KEY (terrain_id),
  CONSTRAINT terrain_map_generated_by_fkey FOREIGN KEY (generated_by) REFERENCES public.users(user_id),
  CONSTRAINT terrain_map_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id)
);

CREATE TABLE public.trade_logs (
  trade_id integer NOT NULL DEFAULT nextval('trade_logs_trade_id_seq'::regclass),
  timestamp timestamp with time zone DEFAULT now(),
  resource USER-DEFINED,
  quantity integer,
  unit_price numeric,
  buyer_id uuid,
  seller_id uuid,
  buyer_alliance_id integer,
  seller_alliance_id integer,
  buyer_name text,
  seller_name text,
  trade_type text DEFAULT 'player_trade'::text CHECK (trade_type = ANY (ARRAY['player_trade'::text, 'market_sale'::text, 'alliance_trade'::text, 'black_market'::text, 'system_grant'::text, 'taxation'::text])),
  trade_status text DEFAULT 'completed'::text CHECK (trade_status = ANY (ARRAY['completed'::text, 'cancelled'::text, 'pending'::text, 'refunded'::text])),
  initiated_by_system boolean DEFAULT false,
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT trade_logs_pkey PRIMARY KEY (trade_id)
);

CREATE TABLE public.training_catalog (
  unit_id integer NOT NULL DEFAULT nextval('training_catalog_unit_id_seq'::regclass),
  unit_name text NOT NULL,
  tier integer,
  training_time integer,
  cost_wood integer DEFAULT 0,
  cost_stone integer DEFAULT 0,
  cost_iron_ore integer DEFAULT 0,
  cost_gold integer DEFAULT 0,
  cost_gems integer DEFAULT 0,
  cost_food integer DEFAULT 0,
  cost_coal integer DEFAULT 0,
  cost_livestock integer DEFAULT 0,
  cost_clay integer DEFAULT 0,
  cost_flax integer DEFAULT 0,
  cost_tools integer DEFAULT 0,
  cost_wood_planks integer DEFAULT 0,
  cost_refined_stone integer DEFAULT 0,
  cost_iron_ingots integer DEFAULT 0,
  cost_charcoal integer DEFAULT 0,
  cost_leather integer DEFAULT 0,
  cost_arrows integer DEFAULT 0,
  cost_swords integer DEFAULT 0,
  cost_axes integer DEFAULT 0,
  cost_shields integer DEFAULT 0,
  cost_armour integer DEFAULT 0,
  cost_wagon integer DEFAULT 0,
  cost_siege_weapons integer DEFAULT 0,
  cost_jewelry integer DEFAULT 0,
  cost_spear integer DEFAULT 0,
  cost_horses integer DEFAULT 0,
  cost_pitchforks integer DEFAULT 0,
  CONSTRAINT training_catalog_pkey PRIMARY KEY (unit_id)
);

CREATE TABLE public.training_history (
  history_id integer NOT NULL DEFAULT nextval('training_history_history_id_seq'::regclass),
  kingdom_id integer,
  unit_id integer,
  unit_name text,
  quantity integer NOT NULL,
  completed_at timestamp with time zone,
  source text DEFAULT 'manual'::text,
  initiated_at timestamp with time zone DEFAULT now(),
  trained_by uuid,
  xp_awarded integer DEFAULT 0,
  modifiers_applied jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT training_history_pkey PRIMARY KEY (history_id),
  CONSTRAINT training_history_trained_by_fkey FOREIGN KEY (trained_by) REFERENCES public.users(user_id),
  CONSTRAINT training_history_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT training_history_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.training_catalog(unit_id)
);

CREATE TABLE public.training_queue (
  queue_id integer NOT NULL DEFAULT nextval('training_queue_queue_id_seq'::regclass),
  kingdom_id integer,
  unit_id integer,
  unit_name text,
  quantity integer NOT NULL,
  training_ends_at timestamp with time zone,
  started_at timestamp with time zone DEFAULT now(),
  status text DEFAULT 'queued'::text CHECK (status = ANY (ARRAY['queued'::text, 'training'::text, 'paused'::text, 'completed'::text, 'cancelled'::text])),
  training_speed_modifier numeric DEFAULT 1.0,
  xp_per_unit integer DEFAULT 0,
  modifiers_applied jsonb DEFAULT '{}'::jsonb,
  initiated_by uuid,
  priority integer DEFAULT 1,
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT training_queue_pkey PRIMARY KEY (queue_id),
  CONSTRAINT training_queue_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT training_queue_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.training_catalog(unit_id),
  CONSTRAINT training_queue_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.unit_counters (
  unit_type text NOT NULL,
  countered_unit_type text NOT NULL,
  effectiveness_multiplier numeric DEFAULT 1.5,
  source text DEFAULT 'base'::text,
  notes text,
  CONSTRAINT unit_counters_pkey PRIMARY KEY (unit_type, countered_unit_type),
  CONSTRAINT unit_counters_unit_type_fkey FOREIGN KEY (unit_type) REFERENCES public.unit_stats(unit_type)
);

CREATE TABLE public.unit_movements (
  movement_id integer NOT NULL DEFAULT nextval('unit_movements_movement_id_seq'::regclass),
  war_id integer,
  kingdom_id integer,
  unit_type text,
  quantity integer,
  position_x integer,
  position_y integer,
  stance text,
  movement_path jsonb,
  target_priority jsonb,
  patrol_zone jsonb,
  fallback_point_x integer,
  fallback_point_y integer,
  withdraw_threshold_percent integer,
  morale double precision,
  status text CHECK (status = ANY (ARRAY['active'::text, 'retreating'::text, 'defeated'::text, 'waiting'::text, 'engaged'::text, 'completed'::text])),
  visible_enemies jsonb DEFAULT '{}'::jsonb,
  unit_level integer DEFAULT 1,
  issued_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT unit_movements_pkey PRIMARY KEY (movement_id),
  CONSTRAINT unit_movements_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id),
  CONSTRAINT unit_movements_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);
CREATE INDEX unit_movements_war_id_idx ON public.unit_movements(war_id);

CREATE TABLE public.unit_stats (
  unit_type text NOT NULL,
  tier integer NOT NULL,
  version_tag text DEFAULT 'v6.12.2025.5.54',
  class text NOT NULL,
  description text,
  hp integer NOT NULL,
  damage integer NOT NULL,
  defense integer NOT NULL,
  speed integer NOT NULL,
  attack_speed numeric NOT NULL,
  range integer NOT NULL,
  vision integer NOT NULL,
  troop_slots integer DEFAULT 1,
  counters ARRAY DEFAULT '{}'::text[],
  is_siege boolean DEFAULT false,
  is_support boolean DEFAULT false,
  icon_path text,
  is_visible boolean DEFAULT true,
  base_training_time integer NOT NULL,
  upkeep_food integer DEFAULT 0,
  upkeep_gold integer DEFAULT 0,
  enabled boolean DEFAULT true,
  last_modified timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  can_build_bridge boolean DEFAULT false,
  can_damage_castle boolean DEFAULT false,
  can_capture_tile boolean DEFAULT true,
  special_traits jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT unit_stats_pkey PRIMARY KEY (unit_type)
);

CREATE TABLE public.unit_upgrade_paths (
  from_unit_type text,
  to_unit_type text,
  cost jsonb DEFAULT '{}'::jsonb,
  required_level integer DEFAULT 1,
  CONSTRAINT unit_upgrade_paths_from_unit_type_fkey FOREIGN KEY (from_unit_type) REFERENCES public.unit_stats(unit_type),
  CONSTRAINT unit_upgrade_paths_to_unit_type_fkey FOREIGN KEY (to_unit_type) REFERENCES public.unit_stats(unit_type)
);

CREATE TABLE public.users (
  user_id uuid NOT NULL,
  username text NOT NULL UNIQUE,
  display_name text,
  kingdom_name text NOT NULL,
  email text NOT NULL UNIQUE,
  profile_bio text,
  profile_picture_url text,
  region text,
  kingdom_id integer,
  alliance_id integer,
  alliance_role text,
  active_policy integer,
  active_laws ARRAY DEFAULT '{}'::integer[],
  is_admin boolean DEFAULT false,
  is_banned boolean DEFAULT false,
  is_deleted boolean DEFAULT false,
  setup_complete boolean DEFAULT false,
  sign_up_date date DEFAULT CURRENT_DATE,
  sign_up_time time without time zone DEFAULT CURRENT_TIME,
  created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
  auth_user_id uuid,
  CONSTRAINT users_pkey PRIMARY KEY (user_id),
  CONSTRAINT users_auth_user_id_fkey FOREIGN KEY (auth_user_id) REFERENCES auth.users(id)
);

CREATE TABLE public.village_buildings (
  village_id integer NOT NULL,
  building_id integer NOT NULL,
  level integer DEFAULT 1,
  construction_started_at timestamp with time zone DEFAULT now(),
  construction_ends_at timestamp with time zone,
  is_under_construction boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  constructed_by uuid,
  active_modifiers jsonb DEFAULT '{}'::jsonb,
  construction_status text DEFAULT 'idle'::text CHECK (construction_status = ANY (ARRAY['idle'::text, 'queued'::text, 'under_construction'::text, 'paused'::text, 'complete'::text])),
  CONSTRAINT village_buildings_pkey PRIMARY KEY (village_id, building_id),
  CONSTRAINT village_buildings_constructed_by_fkey FOREIGN KEY (constructed_by) REFERENCES public.users(user_id),
  CONSTRAINT village_buildings_village_id_fkey FOREIGN KEY (village_id) REFERENCES public.kingdom_villages(village_id),
  CONSTRAINT village_buildings_building_id_fkey FOREIGN KEY (building_id) REFERENCES public.building_catalogue(building_id)
);

CREATE TABLE public.village_modifiers (
  village_id integer NOT NULL,
  resource_bonus jsonb DEFAULT '{}'::jsonb,
  troop_bonus jsonb DEFAULT '{}'::jsonb,
  construction_speed_bonus numeric DEFAULT 0,
  defense_bonus numeric DEFAULT 0,
  trade_bonus numeric DEFAULT 0,
  last_updated timestamp with time zone DEFAULT now(),
  source text DEFAULT 'system'::text,
  stacking_rules jsonb DEFAULT '{}'::jsonb,
  expires_at timestamp with time zone,
  applied_by uuid,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT village_modifiers_pkey PRIMARY KEY (village_id),
  CONSTRAINT village_modifiers_village_id_fkey FOREIGN KEY (village_id) REFERENCES public.kingdom_villages(village_id),
  CONSTRAINT village_modifiers_applied_by_fkey FOREIGN KEY (applied_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.village_production (
  village_id integer NOT NULL,
  resource_type text NOT NULL,
  amount_produced bigint DEFAULT 0,
  last_updated timestamp with time zone DEFAULT now(),
  production_rate numeric DEFAULT 0,
  active_modifiers jsonb DEFAULT '{}'::jsonb,
  last_collected_at timestamp with time zone,
  collection_method text DEFAULT 'automatic'::text,
  created_at timestamp with time zone DEFAULT now(),
  updated_by uuid,
  CONSTRAINT village_production_pkey PRIMARY KEY (village_id, resource_type),
  CONSTRAINT village_production_village_id_fkey FOREIGN KEY (village_id) REFERENCES public.kingdom_villages(village_id),
  CONSTRAINT village_production_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.war_preplans (
  preplan_id integer NOT NULL DEFAULT nextval('war_preplans_preplan_id_seq'::regclass),
  war_id integer,
  kingdom_id integer,
  preplan_jsonb jsonb,
  last_updated timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  submitted_by uuid,
  is_finalized boolean DEFAULT false,
  version integer DEFAULT 1,
  status text DEFAULT 'draft'::text,
  CONSTRAINT war_preplans_pkey PRIMARY KEY (preplan_id),
  CONSTRAINT war_preplans_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id),
  CONSTRAINT war_preplans_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT war_preplans_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.war_scores (
  war_id integer NOT NULL,
  attacker_score integer DEFAULT 0,
  defender_score integer DEFAULT 0,
  victor text CHECK (victor = ANY (ARRAY['attacker'::text, 'defender'::text, 'draw'::text])),
  last_updated timestamp without time zone DEFAULT now(),
  CONSTRAINT war_scores_pkey PRIMARY KEY (war_id),
  CONSTRAINT war_scores_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id)
);
CREATE INDEX war_scores_war_id_idx ON public.war_scores(war_id);

CREATE TABLE public.wars (
  war_id integer NOT NULL DEFAULT nextval('wars_war_id_seq'::regclass),
  attacker_id uuid,
  defender_id uuid,
  attacker_name text,
  defender_name text,
  war_reason text,
  status text,
  start_date timestamp with time zone,
  end_date timestamp with time zone,
  attacker_score integer DEFAULT 0,
  defender_score integer DEFAULT 0,
  attacker_kingdom_id integer,
  defender_kingdom_id integer,
  war_type text DEFAULT 'duel'::text,
  is_retaliation boolean DEFAULT false,
  treaty_triggered boolean DEFAULT false,
  victory_condition text DEFAULT 'score'::text,
  outcome text,
  created_at timestamp with time zone DEFAULT now(),
  last_updated timestamp with time zone DEFAULT now(),
  submitted_by uuid,
  CONSTRAINT wars_pkey PRIMARY KEY (war_id),
  CONSTRAINT wars_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(user_id)
);

CREATE TABLE public.wars_tactical (
  war_id integer NOT NULL DEFAULT nextval('wars_tactical_war_id_seq'::regclass),
  attacker_kingdom_id integer,
  defender_kingdom_id integer,
  phase USER-DEFINED DEFAULT 'alert'::war_phase,
  castle_hp integer DEFAULT 1000,
  battle_tick integer DEFAULT 0,
  war_status USER-DEFINED DEFAULT 'active'::war_status,
  terrain_id integer,
  current_turn text,
  attacker_score integer DEFAULT 0,
  defender_score integer DEFAULT 0,
  last_tick_processed_at timestamp with time zone DEFAULT now(),
  tick_interval_seconds integer DEFAULT 300,
  is_concluded boolean DEFAULT false,
  started_at timestamp with time zone,
  ended_at timestamp with time zone,
  fog_of_war boolean DEFAULT true,
  weather text,
  submitted_by uuid,
  CONSTRAINT wars_tactical_pkey PRIMARY KEY (war_id),
  CONSTRAINT wars_tactical_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars(war_id) ON DELETE CASCADE,
  CONSTRAINT wars_tactical_attacker_kingdom_id_fkey FOREIGN KEY (attacker_kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT wars_tactical_defender_kingdom_id_fkey FOREIGN KEY (defender_kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT wars_tactical_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(user_id),
  CONSTRAINT wars_tactical_terrain_id_fkey FOREIGN KEY (terrain_id) REFERENCES public.terrain_map(terrain_id)
);
```
