CREATE TABLE public.alliance_members (
  alliance_id integer NOT NULL,
  user_id uuid NOT NULL,
  username text,
  rank text,
  contribution integer DEFAULT 0,
  status text,
  crest text,
  CONSTRAINT alliance_members_pkey PRIMARY KEY (alliance_id, user_id),
  CONSTRAINT alliance_members_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
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
  CONSTRAINT alliances_pkey PRIMARY KEY (alliance_id)
);
CREATE TABLE public.audit_log (
  log_id integer NOT NULL DEFAULT nextval('audit_log_log_id_seq'::regclass),
  user_id uuid,
  action text,
  details text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT audit_log_pkey PRIMARY KEY (log_id),
  CONSTRAINT audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
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
  CONSTRAINT black_market_listings_pkey PRIMARY KEY (listing_id),
  CONSTRAINT black_market_listings_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.building_catalogue (
  building_id integer NOT NULL DEFAULT nextval('building_catalogue_building_id_seq'::regclass),
  building_name text NOT NULL,
  description text,
  production_type text,
  production_rate integer,
  upkeep integer,
  build_cost jsonb,
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
CREATE TABLE public.kingdom_buildings (
  kingdom_id integer NOT NULL,
  building_id integer NOT NULL,
  level integer DEFAULT 1,
  CONSTRAINT kingdom_buildings_pkey PRIMARY KEY (kingdom_id, building_id),
  CONSTRAINT kingdom_buildings_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT kingdom_buildings_building_id_fkey FOREIGN KEY (building_id) REFERENCES public.building_catalogue(building_id)
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
CREATE TABLE public.kingdom_troop_slots (
  kingdom_id integer NOT NULL,
  base_slots integer DEFAULT 20,
  used_slots integer DEFAULT 0,
  morale integer DEFAULT 100,
  castle_bonus_slots integer DEFAULT 0,
  noble_bonus_slots integer DEFAULT 0,
  knight_bonus_slots integer DEFAULT 0,
  CONSTRAINT kingdom_troop_slots_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdom_troop_slots_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_castle_progression (
  kingdom_id integer NOT NULL,
  castle_level integer DEFAULT 1,
  xp integer DEFAULT 0,
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_castle_progression_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdom_castle_progression_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_nobles (
  noble_id integer NOT NULL DEFAULT nextval('kingdom_nobles_noble_id_seq'::regclass),
  kingdom_id integer,
  noble_name text,
  title text,
  level integer DEFAULT 1,
  experience integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_nobles_pkey PRIMARY KEY (noble_id),
  CONSTRAINT kingdom_nobles_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

CREATE TABLE public.kingdom_knights (
  knight_id integer NOT NULL DEFAULT nextval('kingdom_knights_knight_id_seq'::regclass),
  kingdom_id integer,
  knight_name text,
  level integer DEFAULT 1,
  experience integer DEFAULT 0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdom_knights_pkey PRIMARY KEY (knight_id),
  CONSTRAINT kingdom_knights_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);
CREATE TABLE public.kingdom_troops (
  kingdom_id integer NOT NULL,
  unit_type text NOT NULL,
  quantity integer DEFAULT 0,
  last_updated timestamp without time zone DEFAULT now(),
  CONSTRAINT kingdom_troops_pkey PRIMARY KEY (kingdom_id, unit_type),
  CONSTRAINT kingdom_troops_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT kingdom_troops_unit_type_fkey FOREIGN KEY (unit_type) REFERENCES public.unit_stats(unit_type)
);
CREATE TABLE public.kingdoms (
  kingdom_id integer NOT NULL DEFAULT nextval('kingdoms_kingdom_id_seq'::regclass),
  user_id uuid,
  kingdom_name text NOT NULL,
  region text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT kingdoms_pkey PRIMARY KEY (kingdom_id),
  CONSTRAINT kingdoms_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id),
  CONSTRAINT kingdoms_user_id_key UNIQUE (user_id)
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
  CONSTRAINT player_messages_pkey PRIMARY KEY (message_id),
  CONSTRAINT player_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id),
  CONSTRAINT player_messages_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.policies_laws_catalogue (
  id integer NOT NULL DEFAULT nextval('policies_laws_catalogue_id_seq'::regclass),
  type text CHECK (type = ANY (ARRAY['policy'::text, 'law'::text])),
  name text NOT NULL,
  description text,
  effect_summary text,
  CONSTRAINT policies_laws_catalogue_pkey PRIMARY KEY (id)
);
CREATE TABLE public.project_player_catalogue (
  project_code text NOT NULL,
  name text NOT NULL,
  description text,
  power_score integer DEFAULT 0,
  cost jsonb,
  required_castle_level integer DEFAULT 0,
  required_nobles integer DEFAULT 0,
  required_knights integer DEFAULT 0,
  CONSTRAINT project_player_catalogue_pkey PRIMARY KEY (project_code)
);
CREATE TABLE public.projects_alliance (
  project_id integer NOT NULL DEFAULT nextval('projects_alliance_project_id_seq'::regclass),
  alliance_id integer,
  name text NOT NULL,
  progress integer DEFAULT 0,
  CONSTRAINT projects_alliance_pkey PRIMARY KEY (project_id),
  CONSTRAINT projects_alliance_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);

CREATE TABLE public.alliance_treaties (
  treaty_id integer NOT NULL DEFAULT nextval('alliance_treaties_treaty_id_seq'::regclass),
  alliance_id integer,
  treaty_type text,
  partner_alliance_id integer,
  status text CHECK (status IN ('proposed','active','cancelled')) DEFAULT 'proposed',
  signed_at timestamp with time zone DEFAULT now(),
  CONSTRAINT alliance_treaties_pkey PRIMARY KEY (treaty_id),
  CONSTRAINT alliance_treaties_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT alliance_treaties_partner_alliance_id_fkey FOREIGN KEY (partner_alliance_id) REFERENCES public.alliances(alliance_id)
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
  CONSTRAINT quest_alliance_catalogue_pkey PRIMARY KEY (quest_code)
);
CREATE TABLE public.quest_alliance_contributions (
  contribution_id integer NOT NULL DEFAULT nextval('quest_alliance_contributions_contribution_id_seq'::regclass),
  alliance_id integer,
  player_name text,
  resource_type USER-DEFINED,
  amount integer,
  timestamp timestamp with time zone DEFAULT now(),
  CONSTRAINT quest_alliance_contributions_pkey PRIMARY KEY (contribution_id),
  CONSTRAINT quest_alliance_contributions_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id)
);
CREATE TABLE public.quest_alliance_tracking (
  alliance_id integer NOT NULL,
  quest_code text NOT NULL,
  status text CHECK (status = ANY (ARRAY['active'::text, 'completed'::text])),
  progress integer DEFAULT 0,
  ends_at timestamp with time zone,
  CONSTRAINT quest_alliance_tracking_pkey PRIMARY KEY (alliance_id, quest_code),
  CONSTRAINT quest_alliance_tracking_alliance_id_fkey FOREIGN KEY (alliance_id) REFERENCES public.alliances(alliance_id),
  CONSTRAINT quest_alliance_tracking_quest_code_fkey FOREIGN KEY (quest_code) REFERENCES public.quest_alliance_catalogue(quest_code)
);
CREATE TABLE public.quest_kingdom_catalogue (
  quest_code text NOT NULL,
  name text NOT NULL,
  description text,
  duration_hours integer,
  required_castle_level integer DEFAULT 0,
  required_nobles integer DEFAULT 0,
  required_knights integer DEFAULT 0,
  CONSTRAINT quest_kingdom_catalogue_pkey PRIMARY KEY (quest_code)
);
CREATE TABLE public.quest_kingdom_tracking (
  kingdom_id integer NOT NULL,
  quest_code text NOT NULL,
  status text CHECK (status = ANY (ARRAY['active'::text, 'completed'::text])),
  progress integer DEFAULT 0,
  ends_at timestamp with time zone,
  CONSTRAINT quest_kingdom_tracking_pkey PRIMARY KEY (kingdom_id, quest_code),
  CONSTRAINT quest_kingdom_tracking_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT quest_kingdom_tracking_quest_code_fkey FOREIGN KEY (quest_code) REFERENCES public.quest_kingdom_catalogue(quest_code)
);
CREATE TABLE public.tech_catalogue (
  tech_code text NOT NULL,
  name text NOT NULL,
  description text,
  category text,
  tier integer,
  duration_hours integer,
  encyclopedia_entry text,
  CONSTRAINT tech_catalogue_pkey PRIMARY KEY (tech_code)
);
CREATE TABLE public.terrain_map (
  terrain_id integer NOT NULL DEFAULT nextval('terrain_map_terrain_id_seq'::regclass),
  war_id integer,
  tile_map jsonb,
  generated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT terrain_map_pkey PRIMARY KEY (terrain_id),
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
  CONSTRAINT trade_logs_pkey PRIMARY KEY (trade_id),
  CONSTRAINT trade_logs_buyer_id_fkey FOREIGN KEY (buyer_id) REFERENCES public.users(user_id),
  CONSTRAINT trade_logs_seller_id_fkey FOREIGN KEY (seller_id) REFERENCES public.users(user_id)
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
  CONSTRAINT training_history_pkey PRIMARY KEY (history_id),
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
  CONSTRAINT training_queue_pkey PRIMARY KEY (queue_id),
  CONSTRAINT training_queue_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT training_queue_unit_id_fkey FOREIGN KEY (unit_id) REFERENCES public.training_catalog(unit_id)
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
  status text,
  visible_enemies jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT unit_movements_pkey PRIMARY KEY (movement_id),
  CONSTRAINT unit_movements_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id),
  CONSTRAINT unit_movements_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);
CREATE TABLE public.unit_stats (
  unit_type text NOT NULL,
  tier integer NOT NULL,
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
CREATE TABLE public.users (
  user_id uuid NOT NULL,
  username text NOT NULL UNIQUE,
  display_name text NOT NULL,
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  kingdom_id integer,
  alliance_id integer,
  alliance_role text,
  active_policy integer,
  active_laws ARRAY DEFAULT '{}'::integer[],
  setup_complete boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.war_preplans (
  preplan_id integer NOT NULL DEFAULT nextval('war_preplans_preplan_id_seq'::regclass),
  war_id integer,
  kingdom_id integer,
  preplan_jsonb jsonb,
  last_updated timestamp with time zone DEFAULT now(),
  CONSTRAINT war_preplans_pkey PRIMARY KEY (preplan_id),
  CONSTRAINT war_preplans_war_id_fkey FOREIGN KEY (war_id) REFERENCES public.wars_tactical(war_id),
  CONSTRAINT war_preplans_kingdom_id_fkey FOREIGN KEY (kingdom_id) REFERENCES public.kingdoms(kingdom_id)
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
  CONSTRAINT wars_pkey PRIMARY KEY (war_id),
  CONSTRAINT wars_attacker_id_fkey FOREIGN KEY (attacker_id) REFERENCES public.users(user_id),
  CONSTRAINT wars_defender_id_fkey FOREIGN KEY (defender_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.wars_tactical (
  war_id integer NOT NULL DEFAULT nextval('wars_tactical_war_id_seq'::regclass),
  attacker_kingdom_id integer,
  defender_kingdom_id integer,
  phase USER-DEFINED DEFAULT 'alert'::war_phase,
  castle_hp integer DEFAULT 1000,
  battle_tick integer DEFAULT 0,
  war_status USER-DEFINED DEFAULT 'active'::war_status,
  CONSTRAINT wars_tactical_pkey PRIMARY KEY (war_id),
  CONSTRAINT wars_tactical_attacker_kingdom_id_fkey FOREIGN KEY (attacker_kingdom_id) REFERENCES public.kingdoms(kingdom_id),
  CONSTRAINT wars_tactical_defender_kingdom_id_fkey FOREIGN KEY (defender_kingdom_id) REFERENCES public.kingdoms(kingdom_id)
);

-- Alliance Vault Transaction Log
CREATE TABLE public.alliance_vault_transaction_log (
  transaction_id bigserial PRIMARY KEY,
  alliance_id integer REFERENCES public.alliances(alliance_id),
  user_id uuid REFERENCES public.users(user_id),
  action text NOT NULL CHECK (action IN ('deposit','withdraw','transfer','trade')),
  resource_type text NOT NULL,
  amount bigint NOT NULL,
  notes text,
  created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX alliance_vault_transaction_log_alliance_id_idx ON public.alliance_vault_transaction_log(alliance_id);

