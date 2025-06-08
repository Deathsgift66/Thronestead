-- db_schema.sql --- Comprehensive schema for Kingmaker's Rise
-- This schema targets PostgreSQL (compatible with Supabase)
-- It defines all major tables referenced in the frontend.

-- RESOURCE TYPES -----------------------------------------------------------
CREATE TYPE IF NOT EXISTS resource_type AS ENUM (
    'Wood', 'Stone', 'Iron Ore', 'Gold', 'Gems', 'Food', 'Coal', 'Livestock', 'Clay', 'Flax',
    'Tools', 'Wood Planks', 'Refined Stone', 'Iron Ingots', 'Charcoal', 'Leather', 'Arrows',
    'Swords', 'Axes', 'Shields', 'Armour', 'Wagon', 'Siege Weapons', 'Jewelry', 'Spear',
    'Horses', 'Pitchforks'
);

-- USERS & ACCOUNTS -----------------------------------------------------------
CREATE TABLE users (
    user_id         UUID PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    display_name    TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    kingdom_id      INTEGER,
    alliance_id     INTEGER,
    alliance_role   TEXT,
    active_policy   INTEGER,
    active_laws     INTEGER[] DEFAULT '{}',
    setup_complete  BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- KINGDOMS ------------------------------------------------------------------
CREATE TABLE kingdoms (
    kingdom_id   SERIAL PRIMARY KEY,
    user_id      UUID REFERENCES users(user_id),
    kingdom_name TEXT NOT NULL,
    region       TEXT,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE region_catalogue (
    region_code TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    resource_bonus JSONB DEFAULT '{}'::jsonb,
    troop_bonus INTEGER DEFAULT 0
);


CREATE TABLE kingdom_resources (
    kingdom_id INTEGER PRIMARY KEY REFERENCES kingdoms(kingdom_id),
    wood BIGINT DEFAULT 0,
    stone BIGINT DEFAULT 0,
    iron_ore BIGINT DEFAULT 0,
    gold BIGINT DEFAULT 0,
    gems BIGINT DEFAULT 0,
    food BIGINT DEFAULT 0,
    coal BIGINT DEFAULT 0,
    livestock BIGINT DEFAULT 0,
    clay BIGINT DEFAULT 0,
    flax BIGINT DEFAULT 0,
    tools BIGINT DEFAULT 0,
    wood_planks BIGINT DEFAULT 0,
    refined_stone BIGINT DEFAULT 0,
    iron_ingots BIGINT DEFAULT 0,
    charcoal BIGINT DEFAULT 0,
    leather BIGINT DEFAULT 0,
    arrows BIGINT DEFAULT 0,
    swords BIGINT DEFAULT 0,
    axes BIGINT DEFAULT 0,
    shields BIGINT DEFAULT 0,
    armour BIGINT DEFAULT 0,
    wagon BIGINT DEFAULT 0,
    siege_weapons BIGINT DEFAULT 0,
    jewelry BIGINT DEFAULT 0,
    spear BIGINT DEFAULT 0,
    horses BIGINT DEFAULT 0,
    pitchforks BIGINT DEFAULT 0
);

CREATE TABLE building_catalogue (
    building_id    SERIAL PRIMARY KEY,
    building_name  TEXT NOT NULL,
    description    TEXT,
    production_type TEXT,
    production_rate INTEGER,
    upkeep         INTEGER,
    build_cost     JSONB
);

CREATE TABLE kingdom_buildings (
    kingdom_id  INTEGER REFERENCES kingdoms(kingdom_id),
    building_id INTEGER REFERENCES building_catalogue(building_id),
    level       INTEGER DEFAULT 1,
    PRIMARY KEY (kingdom_id, building_id)
);

-- TROOP TRAINING ------------------------------------------------------------
CREATE TABLE training_catalog (
    unit_id       SERIAL PRIMARY KEY,
    unit_name     TEXT NOT NULL,
    tier          INTEGER,
    training_time INTEGER,
    cost_wood INTEGER DEFAULT 0,
    cost_stone INTEGER DEFAULT 0,
    cost_iron_ore INTEGER DEFAULT 0,
    cost_gold INTEGER DEFAULT 0,
    cost_gems INTEGER DEFAULT 0,
    cost_food INTEGER DEFAULT 0,
    cost_coal INTEGER DEFAULT 0,
    cost_livestock INTEGER DEFAULT 0,
    cost_clay INTEGER DEFAULT 0,
    cost_flax INTEGER DEFAULT 0,
    cost_tools INTEGER DEFAULT 0,
    cost_wood_planks INTEGER DEFAULT 0,
    cost_refined_stone INTEGER DEFAULT 0,
    cost_iron_ingots INTEGER DEFAULT 0,
    cost_charcoal INTEGER DEFAULT 0,
    cost_leather INTEGER DEFAULT 0,
    cost_arrows INTEGER DEFAULT 0,
    cost_swords INTEGER DEFAULT 0,
    cost_axes INTEGER DEFAULT 0,
    cost_shields INTEGER DEFAULT 0,
    cost_armour INTEGER DEFAULT 0,
    cost_wagon INTEGER DEFAULT 0,
    cost_siege_weapons INTEGER DEFAULT 0,
    cost_jewelry INTEGER DEFAULT 0,
    cost_spear INTEGER DEFAULT 0,
    cost_horses INTEGER DEFAULT 0,
    cost_pitchforks INTEGER DEFAULT 0
);

CREATE TABLE training_queue (
    queue_id         SERIAL PRIMARY KEY,
    kingdom_id       INTEGER REFERENCES kingdoms(kingdom_id),
    unit_id          INTEGER REFERENCES training_catalog(unit_id),
    unit_name        TEXT,
    quantity         INTEGER NOT NULL,
    training_ends_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE training_history (
    history_id   SERIAL PRIMARY KEY,
    kingdom_id   INTEGER REFERENCES kingdoms(kingdom_id),
    unit_id      INTEGER REFERENCES training_catalog(unit_id),
    unit_name    TEXT,
    quantity     INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- MILITARY SLOTS ------------------------------------------------------------
CREATE TABLE kingdom_troop_slots (
    kingdom_id INTEGER PRIMARY KEY REFERENCES kingdoms(kingdom_id),
    base_slots INTEGER DEFAULT 20,
    used_slots INTEGER DEFAULT 0,
    morale     INTEGER DEFAULT 100,
    castle_bonus_slots INTEGER DEFAULT 0,
    noble_bonus_slots  INTEGER DEFAULT 0,
    knight_bonus_slots INTEGER DEFAULT 0
);

-- CASTLE PROGRESSION ------------------------------------------------------
CREATE TABLE kingdom_castle_progression (
    kingdom_id    INTEGER PRIMARY KEY REFERENCES kingdoms(kingdom_id),
    castle_level  INTEGER DEFAULT 1,
    xp            INTEGER DEFAULT 0,
    last_updated  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- NOBLES ------------------------------------------------------------------
CREATE TABLE kingdom_nobles (
    noble_id    SERIAL PRIMARY KEY,
    kingdom_id  INTEGER REFERENCES kingdoms(kingdom_id),
    noble_name  TEXT,
    title       TEXT,
    level       INTEGER DEFAULT 1,
    experience  INTEGER DEFAULT 0,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- KNIGHTS -----------------------------------------------------------------
CREATE TABLE kingdom_knights (
    knight_id   SERIAL PRIMARY KEY,
    kingdom_id  INTEGER REFERENCES kingdoms(kingdom_id),
    knight_name TEXT,
    level       INTEGER DEFAULT 1,
    experience  INTEGER DEFAULT 0,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- TECHNOLOGY & RESEARCH -----------------------------------------------------
CREATE TABLE tech_catalogue (
    tech_code        TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    description      TEXT,
    category         TEXT,
    tier             INTEGER,
    duration_hours   INTEGER,
    encyclopedia_entry TEXT
);

CREATE TABLE kingdom_research_tracking (
    kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    tech_code  TEXT REFERENCES tech_catalogue(tech_code),
    status     TEXT CHECK (status IN ('active','completed','locked')),
    progress   INTEGER DEFAULT 0,
    ends_at    TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (kingdom_id, tech_code)
);

-- PROJECTS ------------------------------------------------------------------
CREATE TABLE project_player_catalogue (
    project_code TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT,
    power_score  INTEGER DEFAULT 0,
    cost         JSONB,
    required_castle_level INTEGER DEFAULT 0,
    required_nobles INTEGER DEFAULT 0,
    required_knights INTEGER DEFAULT 0
);

CREATE TABLE projects_player (
    project_id   SERIAL PRIMARY KEY,
    kingdom_id   INTEGER REFERENCES kingdoms(kingdom_id),
    project_code TEXT REFERENCES project_player_catalogue(project_code),
    power_score  INTEGER DEFAULT 0,
    starts_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ends_at      TIMESTAMP WITH TIME ZONE
);

-- QUESTS --------------------------------------------------------------------
CREATE TABLE quest_kingdom_catalogue (
    quest_code     TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    description    TEXT,
    duration_hours INTEGER,
    required_castle_level INTEGER DEFAULT 0,
    required_nobles INTEGER DEFAULT 0,
    required_knights INTEGER DEFAULT 0
);

CREATE TABLE quest_kingdom_tracking (
    kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    quest_code TEXT REFERENCES quest_kingdom_catalogue(quest_code),
    status     TEXT CHECK (status IN ('active','completed')),
    progress   INTEGER DEFAULT 0,
    ends_at    TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (kingdom_id, quest_code)
);

-- POLICIES & LAWS -----------------------------------------------------------
CREATE TABLE policies_laws_catalogue (
    id             SERIAL PRIMARY KEY,
    type           TEXT CHECK (type IN ('policy','law')),
    name           TEXT NOT NULL,
    description    TEXT,
    effect_summary TEXT
);

-- ALLIANCES -----------------------------------------------------------------
CREATE TABLE alliances (
    alliance_id SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    leader      TEXT,
    status      TEXT,
    region      TEXT,
    level       INTEGER DEFAULT 1,
    motd        TEXT,
    banner      TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    military_score INTEGER DEFAULT 0,
    economy_score  INTEGER DEFAULT 0,
    diplomacy_score INTEGER DEFAULT 0,
    wars_count      INTEGER DEFAULT 0,
    treaties_count  INTEGER DEFAULT 0,
    projects_active INTEGER DEFAULT 0
);

CREATE TABLE alliance_members (
    alliance_id INTEGER REFERENCES alliances(alliance_id),
    user_id     UUID REFERENCES users(user_id),
    username    TEXT,
    rank        TEXT,
    contribution INTEGER DEFAULT 0,
    status      TEXT,
    crest       TEXT,
    PRIMARY KEY (alliance_id, user_id)
);

CREATE TABLE alliance_vault (
    alliance_id       INTEGER PRIMARY KEY REFERENCES alliances(alliance_id),
    wood              BIGINT DEFAULT 0,
    stone             BIGINT DEFAULT 0,
    iron_ore          BIGINT DEFAULT 0,
    gold              BIGINT DEFAULT 0,
    gems              BIGINT DEFAULT 0,
    food              BIGINT DEFAULT 0,
    coal              BIGINT DEFAULT 0,
    livestock         BIGINT DEFAULT 0,
    clay              BIGINT DEFAULT 0,
    flax              BIGINT DEFAULT 0,
    tools             BIGINT DEFAULT 0,
    wood_planks       BIGINT DEFAULT 0,
    refined_stone     BIGINT DEFAULT 0,
    iron_ingots       BIGINT DEFAULT 0,
    charcoal          BIGINT DEFAULT 0,
    leather           BIGINT DEFAULT 0,
    arrows            BIGINT DEFAULT 0,
    swords            BIGINT DEFAULT 0,
    axes              BIGINT DEFAULT 0,
    shields           BIGINT DEFAULT 0,
    armour            BIGINT DEFAULT 0,
    wagon             BIGINT DEFAULT 0,
    siege_weapons     BIGINT DEFAULT 0,
    jewelry           BIGINT DEFAULT 0,
    spear             BIGINT DEFAULT 0,
    horses            BIGINT DEFAULT 0,
    pitchforks        BIGINT DEFAULT 0
    fortification_level INTEGER DEFAULT 0,
    army_count          INTEGER DEFAULT 0,
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE projects_alliance (
    project_id  SERIAL PRIMARY KEY,
    alliance_id INTEGER REFERENCES alliances(alliance_id),
    name        TEXT NOT NULL,
    progress    INTEGER DEFAULT 0
);

-- Alliance Treaties
CREATE TABLE alliance_treaties (
    treaty_id SERIAL PRIMARY KEY,
    alliance_id INTEGER REFERENCES alliances(alliance_id),
    treaty_type TEXT,
    partner_alliance_id INTEGER REFERENCES alliances(alliance_id),
    status TEXT CHECK (status IN ('proposed','active','cancelled')) DEFAULT 'proposed',
    signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alliance Quests
CREATE TABLE quest_alliance_catalogue (
    quest_code     TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    description    TEXT,
    duration_hours INTEGER
);

CREATE TABLE quest_alliance_tracking (
    alliance_id INTEGER REFERENCES alliances(alliance_id),
    quest_code  TEXT REFERENCES quest_alliance_catalogue(quest_code),
    status      TEXT CHECK (status IN ('active','completed')),
    progress    INTEGER DEFAULT 0,
    ends_at     TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (alliance_id, quest_code)
);

CREATE TABLE quest_alliance_contributions (
    contribution_id SERIAL PRIMARY KEY,
    alliance_id     INTEGER REFERENCES alliances(alliance_id),
    player_name     TEXT,
    resource_type   resource_type,
    amount          INTEGER,
    timestamp       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alliance Tax Collections
CREATE TABLE alliance_tax_collections (
    collection_id   SERIAL PRIMARY KEY,
    alliance_id     INTEGER REFERENCES alliances(alliance_id),
    user_id         UUID REFERENCES users(user_id),
    resource_type   resource_type,
    amount_collected INTEGER,
    collected_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source          TEXT,
    notes           TEXT
);

-- MESSAGING -----------------------------------------------------------------
CREATE TABLE player_messages (
    message_id   SERIAL PRIMARY KEY,
    user_id      UUID REFERENCES users(user_id),
    recipient_id UUID REFERENCES users(user_id),
    message      TEXT,
    sent_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read      BOOLEAN DEFAULT FALSE
);

-- TRADE & MARKET ------------------------------------------------------------
CREATE TABLE trade_logs (
    trade_id           SERIAL PRIMARY KEY,
    timestamp          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resource           resource_type,
    quantity           INTEGER,
    unit_price         NUMERIC(12,2),
    buyer_id           UUID REFERENCES users(user_id),
    seller_id          UUID REFERENCES users(user_id),
    buyer_alliance_id  INTEGER,
    seller_alliance_id INTEGER,
    buyer_name         TEXT,
    seller_name        TEXT
);

CREATE TABLE black_market_listings (
    listing_id SERIAL PRIMARY KEY,
    seller_id  UUID REFERENCES users(user_id),
    item       TEXT,
    price      NUMERIC(12,2),
    quantity   INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- WARS ----------------------------------------------------------------------
CREATE TABLE wars (
    war_id          SERIAL PRIMARY KEY,
    attacker_id     UUID REFERENCES users(user_id),
    defender_id     UUID REFERENCES users(user_id),
    attacker_name   TEXT,
    defender_name   TEXT,
    war_reason      TEXT,
    status          TEXT,
    start_date      TIMESTAMP WITH TIME ZONE,
    end_date        TIMESTAMP WITH TIME ZONE,
    attacker_score  INTEGER DEFAULT 0,
    defender_score  INTEGER DEFAULT 0
);

-- NOTIFICATIONS -------------------------------------------------------------
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id         UUID REFERENCES users(user_id),
    title           TEXT,
    message         TEXT,
    category        TEXT,
    priority        TEXT,
    link_action     TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read         BOOLEAN DEFAULT FALSE
);

-- AUDIT LOG -----------------------------------------------------------------
CREATE TABLE audit_log (
    log_id      SERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(user_id),
    action      TEXT,
    details     TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ROW LEVEL SECURITY POLICIES ------------------------------------------------

-- Users table: players can only access their own user row
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY select_own_user ON users
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_user ON users
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_user ON users
  FOR UPDATE USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_own_user ON users
  FOR DELETE USING (auth.uid() = user_id);

-- Kingdoms table
ALTER TABLE kingdoms ENABLE ROW LEVEL SECURITY;
CREATE POLICY select_own_kingdom ON kingdoms
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_kingdom ON kingdoms
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_kingdom ON kingdoms
  FOR UPDATE USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
CREATE POLICY delete_own_kingdom ON kingdoms
  FOR DELETE USING (auth.uid() = user_id);

-- Kingdom resources
ALTER TABLE kingdom_resources ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_resources ON kingdom_resources
  FOR ALL USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = kingdom_resources.kingdom_id
    )
  ) WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = kingdom_resources.kingdom_id
    )
  );

-- Kingdom buildings
ALTER TABLE kingdom_buildings ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_buildings ON kingdom_buildings
  FOR ALL USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = kingdom_buildings.kingdom_id
    )
  ) WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = kingdom_buildings.kingdom_id
    )
  );

-- Training queue
ALTER TABLE training_queue ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_training_queue ON training_queue
  FOR ALL USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = training_queue.kingdom_id
    )
  ) WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = training_queue.kingdom_id
    )
  );

-- Training history
ALTER TABLE training_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_training_history ON training_history
  FOR SELECT USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = training_history.kingdom_id
    )
  );

-- Research tracking
ALTER TABLE kingdom_research_tracking ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_research ON kingdom_research_tracking
  FOR ALL USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = kingdom_research_tracking.kingdom_id
    )
  ) WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = kingdom_research_tracking.kingdom_id
    )
  );

-- Player projects
ALTER TABLE projects_player ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_projects ON projects_player
  FOR ALL USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = projects_player.kingdom_id
    )
  ) WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = projects_player.kingdom_id
    )
  );

-- Kingdom quests
ALTER TABLE quest_kingdom_tracking ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_kingdom_quests ON quest_kingdom_tracking
  FOR ALL USING (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = quest_kingdom_tracking.kingdom_id
    )
  ) WITH CHECK (
    auth.uid() = (
      SELECT user_id FROM kingdoms k
      WHERE k.kingdom_id = quest_kingdom_tracking.kingdom_id
    )
  );

-- Alliance membership and vault
ALTER TABLE alliance_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_membership ON alliance_members
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

ALTER TABLE alliance_vault ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_alliance_vault ON alliance_vault
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = alliance_vault.alliance_id
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = alliance_vault.alliance_id
        AND m.user_id = auth.uid()
    )
  );

-- Alliance quests
ALTER TABLE quest_alliance_tracking ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_alliance_quest ON quest_alliance_tracking
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = quest_alliance_tracking.alliance_id
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = quest_alliance_tracking.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE quest_alliance_contributions ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_alliance_contribs ON quest_alliance_contributions
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = quest_alliance_contributions.alliance_id
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = quest_alliance_contributions.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE alliance_tax_collections ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_alliance_tax ON alliance_tax_collections
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = alliance_tax_collections.alliance_id
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM alliance_members m
      WHERE m.alliance_id = alliance_tax_collections.alliance_id
        AND m.user_id = auth.uid()
    )
  );

-- Player messages
ALTER TABLE player_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_messages ON player_messages
  FOR SELECT USING (auth.uid() = user_id OR auth.uid() = recipient_id);
CREATE POLICY modify_own_messages ON player_messages
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Trade logs
ALTER TABLE trade_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_trade_logs ON trade_logs
  FOR SELECT USING (auth.uid() = buyer_id OR auth.uid() = seller_id);

-- Black market listings
ALTER TABLE black_market_listings ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_black_market_listings ON black_market_listings
  FOR ALL USING (auth.uid() = seller_id)
  WITH CHECK (auth.uid() = seller_id);

-- Wars
ALTER TABLE wars ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_wars ON wars
  FOR SELECT USING (auth.uid() = attacker_id OR auth.uid() = defender_id);

-- Notifications
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_notifications ON notifications
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY modify_own_notifications ON notifications
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Audit log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_audit_log ON audit_log
  FOR SELECT USING (auth.uid() = user_id);

-- TILE BATTLE SYSTEM TABLES ---------------------------------------------------

CREATE TYPE war_phase AS ENUM ('alert', 'planning', 'battle', 'completed');
CREATE TYPE war_status AS ENUM ('active', 'completed');

CREATE TABLE wars_tactical (
    war_id SERIAL PRIMARY KEY,
    attacker_kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    defender_kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    phase war_phase DEFAULT 'alert',
    castle_hp INTEGER DEFAULT 1000,
    battle_tick INTEGER DEFAULT 0,
    war_status war_status DEFAULT 'active'
);

CREATE TABLE unit_movements (
    movement_id SERIAL PRIMARY KEY,
    war_id INTEGER REFERENCES wars_tactical(war_id),
    kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    unit_type TEXT,
    quantity INTEGER,
    position_x INTEGER,
    position_y INTEGER,
    stance TEXT,
    movement_path JSONB,
    target_priority JSONB,
    patrol_zone JSONB,
    fallback_point_x INTEGER,
    fallback_point_y INTEGER,
    withdraw_threshold_percent INTEGER,
    morale FLOAT,
    status TEXT
);

CREATE TABLE terrain_map (
    terrain_id SERIAL PRIMARY KEY,
    war_id INTEGER REFERENCES wars_tactical(war_id),
    tile_map JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE combat_logs (
    combat_id SERIAL PRIMARY KEY,
    war_id INTEGER REFERENCES wars_tactical(war_id),
    tick_number INTEGER,
    event_type TEXT,
    attacker_unit_id INTEGER,
    defender_unit_id INTEGER,
    position_x INTEGER,
    position_y INTEGER,
    damage_dealt INTEGER,
    morale_shift FLOAT,
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE war_preplans (
    preplan_id SERIAL PRIMARY KEY,
    war_id INTEGER REFERENCES wars_tactical(war_id),
    kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    preplan_jsonb JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alliance War Participants -------------------------------------------------
CREATE TABLE alliance_war_participants (
    alliance_war_id INTEGER REFERENCES alliance_wars(alliance_war_id) ON DELETE CASCADE,
    kingdom_id INTEGER REFERENCES kingdoms(kingdom_id),
    role TEXT CHECK (role IN ('attacker','defender')),
    PRIMARY KEY (alliance_war_id, kingdom_id)
);

CREATE INDEX alliance_war_participants_alliance_war_id_idx ON alliance_war_participants(alliance_war_id);
