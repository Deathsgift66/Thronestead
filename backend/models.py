from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    BigInteger,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from backend.db_base import Base


class Kingdom(Base):
    """Minimal kingdom model for tests and basic relations."""

    __tablename__ = "kingdoms"

    kingdom_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    kingdom_name = Column(String, nullable=False)
    region = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String, unique=True, nullable=False)
    kingdom_name = Column(String)
    profile_bio = Column(Text)
    profile_picture_url = Column(String)
    region = Column(String)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    alliance_role = Column(String)
    active_policy = Column(Integer)
    active_laws = Column(JSONB, default=list)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    setup_complete = Column(Boolean, default=False)
    sign_up_date = Column(Date, server_default=func.current_date())
    sign_up_time = Column(Time(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlayerMessage(Base):
    __tablename__ = "player_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    recipient_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    subject = Column(Text)
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    deleted_by_sender = Column(Boolean, default=False)
    deleted_by_recipient = Column(Boolean, default=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Alliance(Base):
    """Minimal alliance record used for foreign key relations."""

    __tablename__ = "alliances"

    alliance_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    leader = Column(String)
    status = Column(String)
    region = Column(String)
    level = Column(Integer, default=1)
    motd = Column(Text)
    banner = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    military_score = Column(Integer, default=0)
    economy_score = Column(Integer, default=0)
    diplomacy_score = Column(Integer, default=0)
    wars_count = Column(Integer, default=0)
    treaties_count = Column(Integer, default=0)
    projects_active = Column(Integer, default=0)


class AllianceMember(Base):
    """Represents membership information for alliances."""

    __tablename__ = "alliance_members"

    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    username = Column(String)
    rank = Column(String)
    contribution = Column(Integer, default=0)
    status = Column(String)
    crest = Column(String)


class AllianceVault(Base):
    __tablename__ = "alliance_vault"
    alliance_id = Column(Integer, primary_key=True)
    wood = Column(BigInteger, default=0)
    stone = Column(BigInteger, default=0)
    iron_ore = Column(BigInteger, default=0)
    gold = Column(BigInteger, default=0)
    gems = Column(BigInteger, default=0)
    food = Column(BigInteger, default=0)
    coal = Column(BigInteger, default=0)
    livestock = Column(BigInteger, default=0)
    clay = Column(BigInteger, default=0)
    flax = Column(BigInteger, default=0)
    tools = Column(BigInteger, default=0)
    wood_planks = Column(BigInteger, default=0)
    refined_stone = Column(BigInteger, default=0)
    iron_ingots = Column(BigInteger, default=0)
    charcoal = Column(BigInteger, default=0)
    leather = Column(BigInteger, default=0)
    arrows = Column(BigInteger, default=0)
    swords = Column(BigInteger, default=0)
    axes = Column(BigInteger, default=0)
    shields = Column(BigInteger, default=0)
    armour = Column(BigInteger, default=0)
    wagon = Column(BigInteger, default=0)
    siege_weapons = Column(BigInteger, default=0)
    jewelry = Column(BigInteger, default=0)
    spear = Column(BigInteger, default=0)
    horses = Column(BigInteger, default=0)
    pitchforks = Column(BigInteger, default=0)
    fortification_level = Column(Integer, default=0)
    army_count = Column(Integer, default=0)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AllianceVaultTransactionLog(Base):
    __tablename__ = "alliance_vault_transaction_log"
    transaction_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    action = Column(String)
    resource_type = Column(String)
    amount = Column(BigInteger)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TradeLog(Base):
    """Canonical record of all resource trades in the economy."""

    __tablename__ = "trade_logs"

    trade_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    resource = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Numeric)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    buyer_alliance_id = Column(Integer)
    seller_alliance_id = Column(Integer)
    buyer_name = Column(Text)
    seller_name = Column(Text)
    trade_type = Column(String)
    trade_status = Column(String, default="completed")
    initiated_by_system = Column(Boolean, default=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NobleHouse(Base):
    """Represents a noble house or family."""

    __tablename__ = "noble_houses"

    house_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    motto = Column(Text)
    crest = Column(Text)
    region = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectPlayerCatalogue(Base):
    __tablename__ = "project_player_catalogue"

    project_code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    power_score = Column(Integer, default=0)
    cost = Column(JSONB)
    modifiers = Column(JSONB)
    category = Column(String)
    is_repeatable = Column(Boolean, default=False)
    prerequisites = Column(JSONB)
    unlocks = Column(JSONB)
    build_time_seconds = Column(Integer)
    project_duration_seconds = Column(Integer)
    requires_kingdom_level = Column(Integer)
    is_active = Column(Boolean, default=True)
    max_active_instances = Column(Integer)
    required_tech = Column(JSONB)
    requires_region = Column(String)
    effect_summary = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class ProjectAllianceCatalogue(Base):
    __tablename__ = "project_alliance_catalogue"

    project_key = Column(String, primary_key=True)
    project_name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    effect_summary = Column(Text)
    is_repeatable = Column(Boolean, default=False)
    required_tech = Column(JSONB)
    prerequisites = Column(JSONB)
    unlocks = Column(JSONB)
    resource_costs = Column(JSONB)
    build_time_seconds = Column(Integer)
    project_duration_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    modifiers = Column(JSONB)
    requires_alliance_level = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    max_active_instances = Column(Integer)
    expires_at = Column(DateTime(timezone=True))


class ProjectsAlliance(Base):
    """Runtime state of Alliance-level projects."""

    __tablename__ = "projects_alliance"

    project_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    name = Column(String, nullable=False)
    project_key = Column(String, ForeignKey("project_alliance_catalogue.project_key"))
    progress = Column(Integer, default=0)
    modifiers = Column(JSONB, default={})
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=False)
    build_state = Column(String)
    built_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    expires_at = Column(DateTime(timezone=True))
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProjectsAllianceInProgress(Base):
    __tablename__ = "projects_alliance_in_progress"

    progress_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    project_key = Column(String, ForeignKey("project_alliance_catalogue.project_key"))
    progress = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    expected_end = Column(DateTime(timezone=True))
    status = Column(String, default="building")
    built_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class WarsTactical(Base):
    __tablename__ = "wars_tactical"
    war_id = Column(Integer, ForeignKey("wars.war_id"), primary_key=True)
    attacker_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    defender_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    phase = Column(String)
    castle_hp = Column(Integer, default=1000)
    battle_tick = Column(Integer, default=0)
    war_status = Column(String)
    terrain_id = Column(Integer, ForeignKey("terrain_map.terrain_id"))
    current_turn = Column(String)
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    last_tick_processed_at = Column(DateTime(timezone=True))
    tick_interval_seconds = Column(Integer, default=300)
    is_concluded = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    fog_of_war = Column(Boolean, default=False)
    weather = Column(String)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class UnitMovement(Base):
    __tablename__ = "unit_movements"
    movement_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"), index=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    unit_type = Column(String)
    unit_level = Column(Integer)
    quantity = Column(Integer)
    position_x = Column(Integer)
    position_y = Column(Integer)
    stance = Column(String)
    movement_path = Column(JSONB)
    target_priority = Column(JSONB)
    patrol_zone = Column(JSONB)
    fallback_point_x = Column(Integer)
    fallback_point_y = Column(Integer)
    withdraw_threshold_percent = Column(Integer)
    morale = Column(Integer)
    status = Column(String)
    visible_enemies = Column(JSONB, default={})
    issued_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CombatLog(Base):
    __tablename__ = "combat_logs"
    combat_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"), index=True)
    tick_number = Column(Integer)
    event_type = Column(String)
    attacker_unit_id = Column(Integer)
    defender_unit_id = Column(Integer)
    position_x = Column(Integer)
    position_y = Column(Integer)
    damage_dealt = Column(Integer, default=0)
    morale_shift = Column(Integer)
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class AllianceWar(Base):
    __tablename__ = "alliance_wars"
    alliance_war_id = Column(Integer, primary_key=True)
    attacker_alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    defender_alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    phase = Column(String)
    castle_hp = Column(Integer, default=10000)
    battle_tick = Column(Integer, default=0)
    war_status = Column(String)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))


class AllianceWarParticipant(Base):
    __tablename__ = "alliance_war_participants"
    alliance_war_id = Column(
        Integer, ForeignKey("alliance_wars.alliance_war_id"), primary_key=True
    )
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    role = Column(String)


class AllianceWarCombatLog(Base):
    __tablename__ = "alliance_war_combat_logs"
    combat_id = Column(Integer, primary_key=True)
    alliance_war_id = Column(
        Integer, ForeignKey("alliance_wars.alliance_war_id", ondelete="CASCADE")
    )
    tick_number = Column(Integer)
    event_type = Column(String)
    attacker_unit_id = Column(Integer)
    defender_unit_id = Column(Integer)
    position_x = Column(Integer)
    position_y = Column(Integer)
    damage_dealt = Column(Integer, default=0)
    morale_shift = Column(Integer, default=0)
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class AllianceWarPreplan(Base):
    __tablename__ = "alliance_war_preplans"
    preplan_id = Column(Integer, primary_key=True)
    alliance_war_id = Column(Integer, ForeignKey("alliance_wars.alliance_war_id"))
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    preplan_jsonb = Column(JSONB)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class War(Base):
    """Metadata for kingdom level wars."""

    __tablename__ = "wars"

    war_id = Column(Integer, primary_key=True)
    attacker_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    defender_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    attacker_name = Column(String)
    defender_name = Column(String)
    war_reason = Column(Text)
    status = Column(String)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    attacker_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    defender_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    war_type = Column(String)
    is_retaliation = Column(Boolean, default=False)
    treaty_triggered = Column(Boolean, default=False)
    victory_condition = Column(String)
    outcome = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class WarPreplan(Base):
    """Pre‑battle plans for tactical wars."""

    __tablename__ = "war_preplans"

    preplan_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"))
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    preplan_jsonb = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    is_finalized = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    status = Column(String, default="draft")


class AllianceWarScore(Base):
    __tablename__ = "alliance_war_scores"
    alliance_war_id = Column(
        Integer,
        ForeignKey("alliance_wars.alliance_war_id", ondelete="CASCADE"),
        primary_key=True,
    )
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    attacker_kills = Column(Integer, default=0)
    defender_kills = Column(Integer, default=0)
    attacker_losses = Column(Integer, default=0)
    defender_losses = Column(Integer, default=0)
    resources_plundered = Column(Integer, default=0)
    battles_participated = Column(Integer, default=0)
    victor = Column(String)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BattleResolutionLog(Base):
    __tablename__ = "battle_resolution_logs"
    resolution_id = Column(Integer, primary_key=True)
    battle_type = Column(String)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"))
    alliance_war_id = Column(Integer, ForeignKey("alliance_wars.alliance_war_id"))
    winner_side = Column(String)
    total_ticks = Column(Integer, default=0)
    attacker_casualties = Column(Integer, default=0)
    defender_casualties = Column(Integer, default=0)
    loot_summary = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WarScore(Base):
    __tablename__ = "war_scores"
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"), primary_key=True, index=True)
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    victor = Column(String)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TerrainMap(Base):
    __tablename__ = "terrain_map"
    terrain_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"))
    tile_map = Column(JSONB)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    map_width = Column(Integer)
    map_height = Column(Integer)
    map_seed = Column(Integer)
    map_version = Column(Integer, default=1)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    map_name = Column(String)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UnitStat(Base):
    __tablename__ = "unit_stats"
    unit_type = Column(String, primary_key=True)
    tier = Column(Integer)
    version_tag = Column(String, default="v1")
    hp = Column(Integer)
    damage = Column(Integer)
    defense = Column(Integer)
    speed = Column(Integer)
    attack_speed = Column(Integer)
    range = Column(Integer)
    vision = Column(Integer)
    troop_slots = Column(Integer, default=1)
    is_siege = Column(Boolean, default=False)


class KingdomTroop(Base):
    __tablename__ = "kingdom_troops"
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    unit_type = Column(String, ForeignKey("unit_stats.unit_type"), primary_key=True)
    quantity = Column(Integer, default=0)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Notification(Base):
    """Player notifications."""

    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    title = Column(String)
    message = Column(Text)
    category = Column(String)
    priority = Column(String)
    link_action = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    source_system = Column(String)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BlackMarketListing(Base):
    """Active player listings on the Black Market."""

    __tablename__ = "black_market_listings"

    listing_id = Column(Integer, primary_key=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    item = Column(String)
    price = Column(Numeric)
    quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KingdomSpies(Base):
    """Spy force tracking for each kingdom."""

    __tablename__ = "kingdom_spies"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    spy_level = Column(Integer, default=1)
    spy_count = Column(Integer, default=0)
    max_spy_capacity = Column(Integer, default=0)
    spy_xp = Column(Integer, default=0)
    spy_upkeep_gold = Column(Integer, default=0)
    last_mission_at = Column(DateTime(timezone=True))
    cooldown_seconds = Column(Integer, default=0)
    spies_lost = Column(Integer, default=0)
    missions_attempted = Column(Integer, default=0)
    missions_successful = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VillageModifier(Base):
    """Temporary or permanent bonuses applied to a village."""

    __tablename__ = "village_modifiers"

    modifier_id = Column(Integer, primary_key=True)
    village_id = Column(Integer, index=True)
    resource_bonus = Column(JSONB, default={})
    troop_bonus = Column(JSONB, default={})
    construction_speed_bonus = Column(Integer, default=0)
    defense_bonus = Column(Integer, default=0)
    trade_bonus = Column(Integer, default=0)
    source = Column(String)
    stacking_rules = Column(JSONB, default={})
    expires_at = Column(DateTime(timezone=True))
    applied_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VillageProduction(Base):
    """Real-time resource production tracking for each village."""

    __tablename__ = "village_production"

    village_id = Column(
        Integer, ForeignKey("kingdom_villages.village_id"), primary_key=True
    )
    resource_type = Column(String, primary_key=True)
    amount_produced = Column(Numeric, default=0)
    production_rate = Column(Numeric, default=0)
    active_modifiers = Column(JSONB, default={})
    last_collected_at = Column(DateTime(timezone=True))
    collection_method = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class SpyMission(Base):
    """Active and completed spy missions."""

    __tablename__ = "spy_missions"

    mission_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    mission_type = Column(String)
    target_id = Column(Integer)
    status = Column(String, default="active")
    launched_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class GameSetting(Base):
    __tablename__ = "game_settings"

    setting_key = Column(String, primary_key=True)
    setting_value = Column(JSONB)
    setting_type = Column(String)
    description = Column(Text)
    default_value = Column(JSONB)
    is_active = Column(Boolean, default=True)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class KingdomHistoryLog(Base):
    """Chronological history of important events for kingdoms."""

    __tablename__ = "kingdom_history_log"

    log_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    event_type = Column(String)
    event_details = Column(Text)
    event_date = Column(DateTime(timezone=True), server_default=func.now())


class QuestAllianceCatalogue(Base):
    """Master list of all alliance quests available in the game."""

    __tablename__ = "quest_alliance_catalogue"

    quest_code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    duration_hours = Column(Integer)
    category = Column(String)
    objectives = Column(JSONB, default={})
    rewards = Column(JSONB, default={})
    required_level = Column(Integer, default=1)
    repeatable = Column(Boolean, default=True)
    max_attempts = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class QuestAllianceTracking(Base):
    """Tracks progress for quests undertaken by an alliance."""

    __tablename__ = "quest_alliance_tracking"

    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), primary_key=True)
    quest_code = Column(
        String, ForeignKey("quest_alliance_catalogue.quest_code"), primary_key=True
    )
    status = Column(String)
    progress = Column(Integer, default=0)
    ends_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    attempt_count = Column(Integer, default=1)
    reward_claimed = Column(Boolean, default=False)
    started_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class QuestKingdomCatalogue(Base):
    """Master list of quests available to individual kingdoms."""

    __tablename__ = "quest_kingdom_catalogue"

    quest_code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    duration_hours = Column(Integer)
    category = Column(String)
    objectives = Column(JSONB, default={})
    rewards = Column(JSONB, default={})
    required_level = Column(Integer, default=1)
    repeatable = Column(Boolean, default=True)
    max_attempts = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class QuestAllianceContribution(Base):
    """Transaction log of player contributions toward alliance quests."""

    __tablename__ = "quest_alliance_contributions"

    contribution_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    player_name = Column(String)
    resource_type = Column(String)
    amount = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    quest_code = Column(String, ForeignKey("quest_alliance_catalogue.quest_code"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    contribution_type = Column(String, default="resource")


class ProjectAllianceContribution(Base):
    """Logs player resource contributions toward alliance projects."""

    __tablename__ = "project_alliance_contributions"

    contribution_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    player_name = Column(String)
    resource_type = Column(String)
    amount = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    project_key = Column(String, ForeignKey("project_alliance_catalogue.project_key"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    contribution_type = Column(String, default="resource")


class QuestKingdomTracking(Base):
    """Tracks progress for kingdom quests."""

    __tablename__ = "quest_kingdom_tracking"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    quest_code = Column(
        String, ForeignKey("quest_kingdom_catalogue.quest_code"), primary_key=True
    )
    status = Column(String)
    progress = Column(Integer, default=0)
    progress_details = Column(JSONB, default=dict)
    ends_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    attempt_count = Column(Integer, default=1)

    started_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class KingdomTemple(Base):
    __tablename__ = "kingdom_temples"

    temple_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    temple_name = Column(String)
    temple_type = Column(String)
    level = Column(Integer, default=1)
    is_major = Column(Boolean, default=False)
    constructed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    started_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))


class KingdomResources(Base):
    __tablename__ = 'kingdom_resources'

    kingdom_id = Column(Integer, primary_key=True)
    wood = Column(BigInteger, default=0)
    stone = Column(BigInteger, default=0)
    iron_ore = Column(BigInteger, default=0)
    gold = Column(BigInteger, default=0)
    gems = Column(BigInteger, default=0)
    food = Column(BigInteger, default=0)
    coal = Column(BigInteger, default=0)
    livestock = Column(BigInteger, default=0)
    clay = Column(BigInteger, default=0)
    flax = Column(BigInteger, default=0)
    tools = Column(BigInteger, default=0)
    wood_planks = Column(BigInteger, default=0)
    refined_stone = Column(BigInteger, default=0)
    iron_ingots = Column(BigInteger, default=0)
    charcoal = Column(BigInteger, default=0)
    leather = Column(BigInteger, default=0)
    arrows = Column(BigInteger, default=0)
    swords = Column(BigInteger, default=0)
    axes = Column(BigInteger, default=0)
    shields = Column(BigInteger, default=0)
    armour = Column(BigInteger, default=0)
    wagon = Column(BigInteger, default=0)
    siege_weapons = Column(BigInteger, default=0)
    jewelry = Column(BigInteger, default=0)
    spear = Column(BigInteger, default=0)
    horses = Column(BigInteger, default=0)
    pitchforks = Column(BigInteger, default=0)

