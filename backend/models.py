# Project Name: Thronestead©
# File Name: models.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
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
    Float,
    text,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from backend.db_base import Base



class Kingdom(Base):
    """ORM model for the ``kingdoms`` table."""

    __tablename__ = "kingdoms"

    kingdom_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), unique=True)
    kingdom_name = Column(Text, nullable=False)
    region = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    prestige_score = Column(Integer, default=0)
    avatar_url = Column(Text)
    status = Column(Text, server_default="active")
    description = Column(Text)
    motto = Column(Text)
    ruler_name = Column(Text)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    alliance_role = Column(Text)
    tech_level = Column(Integer, default=1)
    economy_score = Column(Integer, default=0)
    military_score = Column(Integer, default=0)
    diplomacy_score = Column(Integer, default=0)
    last_login_at = Column(DateTime(timezone=True))
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    is_npc = Column(Boolean, default=False)
    customizations = Column(JSONB, default=dict)
    ruler_title = Column(Text)
    banner_url = Column(Text)
    emblem_url = Column(Text)
    is_on_vacation = Column(Boolean, default=False)
    vacation_started_at = Column(DateTime(timezone=True))
    vacation_expires_at = Column(DateTime(timezone=True))
    vacation_cooldown_until = Column(DateTime(timezone=True))
    policy_change_allowed_at = Column(DateTime(timezone=True))
    banner_color = Column(Text)
    national_theme = Column(Text)


class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String)
    email = Column(String, unique=True, nullable=False)
    kingdom_name = Column(String, nullable=False)
    profile_bio = Column(Text)
    profile_picture_url = Column(String)
    region = Column(String)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    alliance_role = Column(String)
    active_policy = Column(Integer)
    active_laws = Column(ARRAY(Integer), server_default=text("'{}'"))
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    setup_complete = Column(Boolean, default=False)
    sign_up_date = Column(Date, server_default=func.current_date())
    sign_up_time = Column(Time(timezone=False), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    auth_user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    active_policy_1 = Column(String)
    active_policy_2 = Column(String)


class PlayerMessage(Base):
    __tablename__ = "player_messages"

    message_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)



class Announcement(Base):
    """Public announcements shown on the login screen."""

    __tablename__ = "announcements"

    announcement_id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    visible = Column(Boolean, default=True)


class PoliciesLawsCatalogue(Base):
    __tablename__ = "policies_laws_catalogue"

    id = Column(Integer, primary_key=True)
    type = Column(Text)
    name = Column(Text, nullable=False)
    description = Column(Text)
    effect_summary = Column(Text)


class PolicyChangeLog(Base):
    __tablename__ = "policy_change_log"

    log_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer)
    alliance_id = Column(Integer)
    policy_id = Column(Integer)
    changed_by = Column(UUID(as_uuid=True))
    change_type = Column(Text)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class UserSettingEntry(Base):
    __tablename__ = "user_setting_entries"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    setting_key = Column(String, primary_key=True)
    setting_value = Column(Text)


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True))
    action = Column(Text)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    kingdom_id = Column(Integer)


class ArchivedAuditLog(Base):
    __tablename__ = "archived_audit_log"

    log_id = Column(BigInteger)
    user_id = Column(UUID(as_uuid=True))
    action = Column(Text)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True))


class GlobalEvent(Base):
    """Scheduled world events that impact gameplay."""

    __tablename__ = "global_events"

    event_id = Column(Integer, primary_key=True)
    name = Column(Text)
    description = Column(Text)
    start_time = Column(DateTime(timezone=False))
    end_time = Column(DateTime(timezone=False))
    is_active = Column(Boolean, server_default="false")
    impact_type = Column(Text)
    magnitude = Column(Numeric)


class KingdomAchievementCatalogue(Base):
    __tablename__ = "kingdom_achievement_catalogue"

    achievement_code = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(Text)
    reward = Column(JSONB, server_default="{}")
    points = Column(Integer, server_default="0")
    is_hidden = Column(Boolean, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    gold_reward = Column(Integer, server_default="0")
    honor_reward = Column(Integer, server_default="0")


class KingdomAchievement(Base):
    __tablename__ = "kingdom_achievements"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    achievement_code = Column(
        Text,
        ForeignKey("kingdom_achievement_catalogue.achievement_code"),
        primary_key=True,
    )
    awarded_at = Column(DateTime(timezone=True), server_default=func.now())

class MessageMetadata(Base):
    """Key/value metadata attached to ``player_messages``."""

    __tablename__ = "message_metadata"

    message_id = Column(
        Integer,
        ForeignKey("player_messages.message_id"),
        primary_key=True,
    )
    key = Column(Text, primary_key=True)
    value = Column(Text)




class Alliance(Base):
    """Minimal alliance record used for foreign key relations."""

    __tablename__ = "alliances"

    alliance_id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    leader = Column(Text)
    status = Column(Text)
    region = Column(Text)
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
    emblem_url = Column(Text)


class AllianceMember(Base):
    """Represents membership information for alliances."""

    __tablename__ = "alliance_members"
    __table_args__ = (
        Index("idx_alliance_members_user_id", "user_id"),
        Index("idx_alliance_members_alliance_id", "alliance_id"),
        Index("idx_alliance_members_contribution", "contribution"),
    )

    alliance_id = Column(
        Integer, ForeignKey("alliances.alliance_id"), primary_key=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True
    )
    username = Column(String)
    rank = Column(String)
    contribution = Column(Integer, default=0)
    status = Column(String)
    crest = Column(String)
    role_id = Column(Integer, ForeignKey("alliance_roles.role_id"))


class AllianceRole(Base):
    __tablename__ = "alliance_roles"

    role_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    role_name = Column(Text, nullable=False)
    permissions = Column(JSONB, server_default=text("'{}'::jsonb"))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    can_invite = Column(Boolean, default=False)
    can_kick = Column(Boolean, default=False)
    can_manage_resources = Column(Boolean, default=False)


class AlliancePolicy(Base):
    __tablename__ = "alliance_policies"

    alliance_id = Column(
        Integer, ForeignKey("alliances.alliance_id"), primary_key=True
    )
    policy_id = Column(
        Integer, ForeignKey("policies_laws_catalogue.id"), primary_key=True
    )
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)



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
    transaction_id = Column(BigInteger, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    action = Column(Text)
    resource_type = Column(Text)
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
    trade_type = Column(String, server_default=text("'player_trade'"))
    trade_status = Column(String, server_default=text("'completed'"))
    initiated_by_system = Column(Boolean, default=False)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )



class AllianceBlacklist(Base):
    __tablename__ = "alliance_blacklist"

    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), primary_key=True)
    target_alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), primary_key=True)
    reason = Column(Text)
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class AllianceGrant(Base):
    __tablename__ = "alliance_grants"

    grant_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), nullable=False)
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    resource_type = Column(Text, nullable=False)
    amount = Column(BigInteger, default=0)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(Text)


class AllianceLoan(Base):
    __tablename__ = "alliance_loans"

    loan_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), nullable=False)
    borrower_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    resource_type = Column(Text, nullable=False)
    amount = Column(BigInteger, default=0)
    amount_repaid = Column(BigInteger, default=0)
    interest_rate = Column(Numeric, default=0.05)
    due_date = Column(DateTime(timezone=True))
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    default_penalty_rate = Column(Numeric, default=0.10)
    is_tax_active = Column(Boolean, default=False)
    tax_started_at = Column(DateTime(timezone=True))


class AllianceVote(Base):
    __tablename__ = "alliance_votes"

    vote_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    proposal_type = Column(Text)
    proposal_details = Column(JSONB)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ends_at = Column(DateTime(timezone=True))
    status = Column(Text, default="active")
    vote_type = Column(Text)
    target_id = Column(Integer)
    vote_metadata = Column(Text)


class AllianceVoteParticipant(Base):
    __tablename__ = "alliance_vote_participants"

    vote_id = Column(Integer, ForeignKey("alliance_votes.vote_id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    vote_choice = Column(Text)
    voted_at = Column(DateTime(timezone=True), server_default=func.now())


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


class RegionCatalogue(Base):
    """Catalogue of regions players can choose from."""

    __tablename__ = "region_catalogue"

    region_code = Column(String, primary_key=True)
    region_name = Column(String, nullable=False)
    description = Column(Text)
    wood_bonus = Column(Numeric, default=0)
    iron_bonus = Column(Numeric, default=0)
    troop_attack_bonus = Column(Numeric, default=0)


class RegionStructure(Base):
    __tablename__ = "region_structures"

    region_code = Column(
        String,
        ForeignKey("region_catalogue.region_code"),
        primary_key=True,
    )
    structure_type = Column(String, primary_key=True)
    structure_level = Column(Integer)


class ProjectPlayerCatalogue(Base):
    __tablename__ = "project_player_catalogue"

    project_code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    power_score = Column(Integer, server_default="0")
    cost = Column(JSONB)
    modifiers = Column(JSONB, server_default="{}")
    category = Column(String)
    is_repeatable = Column(Boolean, server_default="true")
    prerequisites = Column(ARRAY(Text))
    unlocks = Column(ARRAY(Text))
    build_time_seconds = Column(Integer, server_default="3600")
    project_duration_seconds = Column(Integer)
    requires_kingdom_level = Column(Integer, server_default="1")
    is_active = Column(Boolean, server_default="true")
    max_active_instances = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    required_tech = Column(ARRAY(Text))
    requires_region = Column(String)
    effect_summary = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    last_modified_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    gold_cost = Column(Integer, server_default="0")
    effect_description = Column(Text)
    wood = Column(Integer, server_default="0")
    stone = Column(Integer, server_default="0")
    iron_ore = Column(Integer, server_default="0")
    gold = Column(Integer, server_default="0")
    gems = Column(Integer, server_default="0")
    food = Column(Integer, server_default="0")
    coal = Column(Integer, server_default="0")
    livestock = Column(Integer, server_default="0")
    clay = Column(Integer, server_default="0")
    flax = Column(Integer, server_default="0")
    tools = Column(Integer, server_default="0")
    wood_planks = Column(Integer, server_default="0")
    refined_stone = Column(Integer, server_default="0")
    iron_ingots = Column(Integer, server_default="0")
    charcoal = Column(Integer, server_default="0")
    leather = Column(Integer, server_default="0")
    arrows = Column(Integer, server_default="0")
    swords = Column(Integer, server_default="0")
    axes = Column(Integer, server_default="0")
    shields = Column(Integer, server_default="0")
    armour = Column(Integer, server_default="0")
    wagon = Column(Integer, server_default="0")
    siege_weapons = Column(Integer, server_default="0")
    jewelry = Column(Integer, server_default="0")
    spear = Column(Integer, server_default="0")
    horses = Column(Integer, server_default="0")
    pitchforks = Column(Integer, server_default="0")


class ProjectAllianceCatalogue(Base):
    __tablename__ = "project_alliance_catalogue"

    project_id = Column(Integer, primary_key=True)
    project_key = Column(Text, unique=True, nullable=False)
    project_name = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(Text)
    effect_summary = Column(Text)
    is_repeatable = Column(Boolean, default=False)
    required_tech = Column(ARRAY(Text))
    prerequisites = Column(ARRAY(Text))
    unlocks = Column(ARRAY(Text))
    resource_costs = Column(JSONB)
    build_time_seconds = Column(Integer)
    project_duration_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    requires_alliance_level = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    max_active_instances = Column(Integer)
    expires_at = Column(DateTime(timezone=True))
    wood_cost = Column(Integer, default=0)
    stone_cost = Column(Integer, default=0)
    effect_description = Column(Text)
    wood = Column(Integer, default=0)
    stone = Column(Integer, default=0)
    iron_ore = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    gems = Column(Integer, default=0)
    food = Column(Integer, default=0)
    coal = Column(Integer, default=0)
    livestock = Column(Integer, default=0)
    clay = Column(Integer, default=0)
    flax = Column(Integer, default=0)
    tools = Column(Integer, default=0)
    wood_planks = Column(Integer, default=0)
    refined_stone = Column(Integer, default=0)
    iron_ingots = Column(Integer, default=0)
    charcoal = Column(Integer, default=0)
    leather = Column(Integer, default=0)
    arrows = Column(Integer, default=0)
    swords = Column(Integer, default=0)
    axes = Column(Integer, default=0)
    shields = Column(Integer, default=0)
    armour = Column(Integer, default=0)
    wagon = Column(Integer, default=0)
    siege_weapons = Column(Integer, default=0)
    jewelry = Column(Integer, default=0)
    spear = Column(Integer, default=0)
    horses = Column(Integer, default=0)
    pitchforks = Column(Integer, default=0)


class ProjectsAlliance(Base):
    """Runtime state of Alliance-level projects."""

    __tablename__ = "projects_alliance"

    project_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    name = Column(String, nullable=False)
    project_key = Column(Text, ForeignKey("project_alliance_catalogue.project_key"))
    progress = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    build_state = Column(String, server_default="queued")
    built_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    expires_at = Column(DateTime(timezone=True))
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    active_bonus = Column(Text)


class ProjectsAllianceInProgress(Base):
    __tablename__ = "projects_alliance_in_progress"

    progress_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    project_key = Column(Text, ForeignKey("project_alliance_catalogue.project_key"))
    progress = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=False), server_default=func.now())
    expected_end = Column(DateTime(timezone=False))
    status = Column(String, default="building")
    built_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class WarsTactical(Base):
    __tablename__ = "wars_tactical"
    war_id = Column(Integer, ForeignKey("wars.war_id"), primary_key=True)
    attacker_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    defender_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    phase = Column(String, server_default="alert")
    castle_hp = Column(Integer, default=1000)
    battle_tick = Column(Integer, default=0)
    war_status = Column(String, server_default="active")
    terrain_id = Column(Integer, ForeignKey("terrain_map.terrain_id"))
    current_turn = Column(String)
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    last_tick_processed_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    tick_interval_seconds = Column(Integer, default=300)
    is_concluded = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    fog_of_war = Column(Boolean, default=True)
    weather = Column(Text)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class UnitMovement(Base):
    __tablename__ = "unit_movements"
    __table_args__ = (
        Index("idx_unit_movements_war_id", "war_id"),
    )
    movement_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"), index=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    unit_type = Column(String)
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
    morale = Column(Numeric)
    status = Column(String)
    visible_enemies = Column(JSONB, default=dict, server_default="{}")
    unit_level = Column(Integer, default=1)
    issued_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    target_tile_x = Column(Integer)
    target_tile_y = Column(Integer)
    patrol_start_x = Column(Integer)
    patrol_start_y = Column(Integer)


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
    morale_shift = Column(Float)
    notes = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    treaty_trigger_context = Column(JSONB, default=dict)
    triggered_by_treaty = Column(Boolean, default=False)
    treaty_name = Column(Text)


class AllianceWar(Base):
    __tablename__ = "alliance_wars"
    alliance_war_id = Column(Integer, primary_key=True)
    attacker_alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    defender_alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    phase = Column(String, server_default="alert")
    castle_hp = Column(Integer, default=10000)
    battle_tick = Column(Integer, default=0)
    war_status = Column(String, server_default="active")
    start_date = Column(DateTime(timezone=False), server_default=func.now())
    end_date = Column(DateTime(timezone=False))


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
    tick_number = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    attacker_unit_id = Column(Integer)
    defender_unit_id = Column(Integer)
    position_x = Column(Integer)
    position_y = Column(Integer)
    damage_dealt = Column(Integer, default=0)
    morale_shift = Column(Float, default=0)
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
    __table_args__ = (
        CheckConstraint("outcome IN ('attacker','defender','draw')", name="wars_outcome_check"),
    )

    war_id = Column(Integer, primary_key=True)
    attacker_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    defender_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    attacker_name = Column(Text)
    defender_name = Column(Text)
    war_reason = Column(Text)
    status = Column(Text)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    attacker_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    defender_kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    war_type = Column(Text, server_default="duel")
    is_retaliation = Column(Boolean, default=False)
    treaty_triggered = Column(Boolean, default=False)
    victory_condition = Column(Text, server_default="score")
    outcome = Column(Text)
    triggered_by_treaty = Column(Boolean, default=False)
    triggering_treaty_type = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class WarPreplan(Base):
    """Pre-battle plans for tactical wars."""

    __tablename__ = "war_preplans"

    preplan_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"))
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    preplan_jsonb = Column(JSONB)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    is_finalized = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    status = Column(Text, default="draft")
    start_tile_x = Column(Integer)
    start_tile_y = Column(Integer)
    initial_orders = Column(Text)


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
    battle_type = Column(Text)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"))
    alliance_war_id = Column(Integer, ForeignKey("alliance_wars.alliance_war_id"))
    winner_side = Column(Text)
    total_ticks = Column(Integer, default=0)
    attacker_casualties = Column(Integer, default=0)
    defender_casualties = Column(Integer, default=0)
    loot_summary = Column(JSONB, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    gold_looted = Column(Integer, default=0)
    resources_looted = Column(Text)


class WarScore(Base):
    __tablename__ = "war_scores"
    __table_args__ = (
        CheckConstraint("victor IN ('attacker','defender','draw')"),
    )
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"), primary_key=True, index=True)
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    victor = Column(String)
    last_updated = Column(DateTime(timezone=False), server_default=func.now())


class TerrainMap(Base):
    __tablename__ = "terrain_map"
    __table_args__ = (
        Index("idx_terrain_map_war_id", "war_id"),
    )

    terrain_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey("wars_tactical.war_id"), index=True)
    tile_map = Column(JSONB)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    map_width = Column(Integer)
    map_height = Column(Integer)
    map_seed = Column(Integer)
    map_version = Column(Integer, default=1)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    map_name = Column(Text)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    map_type = Column(Text, default="battlefield")
    tile_schema_version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    map_source = Column(Text, default="auto-generated")

    map_features = Column(JSONB, server_default=text("'{}'::jsonb"))
    tileset = Column(Text)
    features_summary = Column(Text)


class UnitStat(Base):
    __tablename__ = "unit_stats"
    unit_type = Column(String, primary_key=True)
    tier = Column(Integer, nullable=False)
    class_ = Column("class", String, nullable=False)
    description = Column(Text)
    hp = Column(Integer, nullable=False)
    damage = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)
    attack_speed = Column(Numeric, nullable=False)
    range = Column(Integer, nullable=False)
    vision = Column(Integer, nullable=False)
    troop_slots = Column(Integer, default=1)
    counters = Column(ARRAY(String), default=list)
    is_siege = Column(Boolean, default=False)
    is_support = Column(Boolean, default=False)
    icon_path = Column(String)
    is_visible = Column(Boolean, default=True)
    base_training_time = Column(Integer, nullable=False)
    upkeep_food = Column(Integer, default=0)
    upkeep_gold = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    last_modified = Column(DateTime, server_default=func.current_timestamp())
    can_build_bridge = Column(Boolean, default=False)
    can_damage_castle = Column(Boolean, default=False)
    can_capture_tile = Column(Boolean, default=True)
    special_traits = Column(JSONB, default=dict)
    is_meta = Column(Boolean, default=False)
    special_ability = Column(String)


class UnitCounter(Base):
    __tablename__ = "unit_counters"
    unit_type = Column(String, ForeignKey("unit_stats.unit_type"), primary_key=True)
    countered_unit_type = Column(
        String, ForeignKey("unit_stats.unit_type"), primary_key=True
    )
    effectiveness_multiplier = Column(Numeric, default=1.5)
    source = Column(String, default="base")
    notes = Column(Text)


class UnitUpgradePath(Base):
    __tablename__ = "unit_upgrade_paths"

    from_unit_type = Column(String, ForeignKey("unit_stats.unit_type"), primary_key=True)
    to_unit_type = Column(String, ForeignKey("unit_stats.unit_type"), primary_key=True)
    cost = Column(JSONB, server_default=text("'{}'::jsonb"))
    required_level = Column(Integer, default=1)
    wood = Column(Integer, default=0)
    stone = Column(Integer, default=0)
    iron_ore = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    gems = Column(Integer, default=0)
    food = Column(Integer, default=0)
    coal = Column(Integer, default=0)
    livestock = Column(Integer, default=0)
    clay = Column(Integer, default=0)
    flax = Column(Integer, default=0)
    tools = Column(Integer, default=0)
    wood_planks = Column(Integer, default=0)
    refined_stone = Column(Integer, default=0)
    iron_ingots = Column(Integer, default=0)
    charcoal = Column(Integer, default=0)
    leather = Column(Integer, default=0)
    arrows = Column(Integer, default=0)
    swords = Column(Integer, default=0)
    axes = Column(Integer, default=0)
    shields = Column(Integer, default=0)
    armour = Column(Integer, default=0)
    wagon = Column(Integer, default=0)
    siege_weapons = Column(Integer, default=0)
    jewelry = Column(Integer, default=0)
    spear = Column(Integer, default=0)
    horses = Column(Integer, default=0)
    pitchforks = Column(Integer, default=0)


class KingdomTroop(Base):
    __tablename__ = "kingdom_troops"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    unit_type = Column(String, ForeignKey("unit_stats.unit_type"), primary_key=True)
    unit_level = Column(Integer, primary_key=True, default=1)
    quantity = Column(Integer, default=0)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    in_training = Column(Integer, default=0)
    wounded = Column(Integer, default=0)
    active_modifiers = Column(JSONB, default=dict)
    last_modified_by = Column(UUID(as_uuid=True))
    last_combat_at = Column(DateTime(timezone=True))
    last_morale = Column(Integer, default=100)
    morale_bonus = Column(Numeric, default=0)
    damage_bonus = Column(Numeric, default=0)


class Notification(Base):
    """Player notifications."""

    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    title = Column(Text)
    message = Column(Text)
    category = Column(Text)
    priority = Column(Text)
    link_action = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    source_system = Column(Text)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificationMetadata(Base):
    """Optional key/value metadata for notifications."""

    __tablename__ = "notification_metadata"

    notification_id = Column(
        Integer,
        ForeignKey("notifications.notification_id"),
        primary_key=True,
    )
    key = Column(Text, primary_key=True)
    value = Column(Text)


class AllianceNotice(Base):
    """Notices shared within alliances or globally."""

    __tablename__ = "alliance_notices"

    notice_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"))
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    category = Column(Text)
    link_action = Column(Text)
    image_url = Column(Text)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class BlackMarketListing(Base):
    """Active player listings on the Black Market."""

    __tablename__ = "black_market_listings"

    listing_id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(UUID(as_uuid=True))
    item = Column(Text)
    price = Column(Numeric)
    quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KingdomSpies(Base):
    """Spy force tracking for each kingdom."""

    __tablename__ = "kingdom_spies"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    spy_level = Column(Integer, default=1)
    spy_count = Column(Integer, default=0)
    max_spy_capacity = Column(Integer, default=10)
    spy_upkeep_gold = Column(Integer, default=0)
    last_mission_at = Column(DateTime(timezone=True))
    cooldown_seconds = Column(Integer, default=0)
    spies_lost = Column(Integer, default=0)
    missions_attempted = Column(Integer, default=0)
    missions_successful = Column(Integer, default=0)
    daily_attacks_sent = Column(Integer, default=0)
    daily_attacks_received = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VillageBuilding(Base):
    """Represents the state of a building within a village."""

    __tablename__ = "village_buildings"

    village_id = Column(
        Integer, ForeignKey("kingdom_villages.village_id"), primary_key=True
    )
    building_id = Column(
        Integer, ForeignKey("building_catalogue.building_id"), primary_key=True
    )
    level = Column(Integer, default=1)
    construction_started_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    construction_ends_at = Column(DateTime(timezone=True))
    is_under_construction = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    constructed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    active_modifiers = Column(JSONB, server_default=text("'{}'::jsonb"))
    construction_status = Column(Text, server_default="idle")
    productivity_bonus = Column(Numeric, default=0)


class VillageModifier(Base):
    """Temporary or permanent bonuses applied to a village."""

    __tablename__ = "village_modifiers"

    village_id = Column(
        Integer, ForeignKey("kingdom_villages.village_id"), primary_key=True
    )
    resource_bonus = Column(JSONB, server_default=text("'{}'::jsonb"))
    troop_bonus = Column(JSONB, server_default=text("'{}'::jsonb"))
    construction_speed_bonus = Column(Numeric, default=0)
    defense_bonus = Column(Numeric, default=0)
    trade_bonus = Column(Numeric, default=0)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    source = Column(Text, server_default="system")
    stacking_rules = Column(JSONB, server_default=text("'{}'::jsonb"))
    expires_at = Column(DateTime(timezone=True))
    applied_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    wood_output_bonus = Column(Numeric, default=0)
    troop_training_speed = Column(Numeric, default=0)


class VillageProduction(Base):
    """Real-time resource production tracking for each village."""

    __tablename__ = "village_production"

    village_id = Column(
        Integer, ForeignKey("kingdom_villages.village_id"), primary_key=True
    )
    resource_type = Column(Text, primary_key=True)
    amount_produced = Column(BigInteger, default=0)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    production_rate = Column(Numeric, default=0)
    active_modifiers = Column(JSONB, server_default=text("'{}'::jsonb"))
    last_collected_at = Column(DateTime(timezone=True))
    collection_method = Column(String, server_default="automatic")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    seasonal_multiplier = Column(Numeric, default=1)


class SpyMission(Base):
    """Active and completed spy missions."""

    __tablename__ = "spy_missions"

    mission_id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('spy_missions_mission_id_seq'::regclass)"),
    )
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    mission_type = Column(String)
    target_id = Column(Integer)
    status = Column(String, server_default="active")
    launched_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class GameSetting(Base):
    __tablename__ = "game_settings"

    setting_key = Column(String, primary_key=True)
    setting_type = Column(String)
    description = Column(Text)
    default_value = Column(JSONB)
    is_active = Column(Boolean, default=True)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    setting_string = Column(String)
    setting_number = Column(Numeric)
    setting_boolean = Column(Boolean, default=False)


class GameSettingValue(Base):
    __tablename__ = "game_setting_values"

    setting_key = Column(
        String,
        ForeignKey("game_settings.setting_key", ondelete="CASCADE"),
        primary_key=True,
    )
    setting_value = Column(Text)


class SystemEventHook(Base):
    """Webhook configuration for system events."""

    __tablename__ = "system_event_hooks"

    hook_id = Column(Integer, primary_key=True)
    event_type = Column(Text)
    payload_template = Column(JSONB)
    endpoint_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    event_topic = Column(Text)
    payload_template_text = Column(Text)


class TechCatalogue(Base):
    """Research technologies available to kingdoms."""

    __tablename__ = "tech_catalogue"

    tech_code = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(Text)
    tier = Column(Integer)
    duration_hours = Column(Integer)
    encyclopedia_entry = Column(Text)
    modifiers = Column(JSONB, server_default=text("'{}'::jsonb"))
    prerequisites = Column(ARRAY(Text))
    required_kingdom_level = Column(Integer, default=1)
    required_region = Column(Text)
    is_repeatable = Column(Boolean, default=False)
    max_research_level = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    military_bonus = Column(Numeric, default=0)
    economic_bonus = Column(Numeric, default=0)


class KingdomHistoryLog(Base):
    """Chronological history of important events for kingdoms."""

    __tablename__ = "kingdom_history_log"

    log_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    event_type = Column(Text)
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
    objective_type = Column(String)
    reward_gold = Column(Integer, default=0)
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
    objective_type = Column(String)
    reward_gold = Column(Integer, default=0)


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
    project_key = Column(Text, ForeignKey("project_alliance_catalogue.project_key"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    contribution_type = Column(String, default="resource")


class ProjectModifier(Base):
    """Modifier entry applied from projects or catalogue items."""

    __tablename__ = "project_modifiers"

    source_type = Column(String, primary_key=True)
    source_id = Column(String, primary_key=True)
    effect_type = Column(String, primary_key=True)
    target = Column(String, primary_key=True)
    magnitude = Column(Numeric)


class QuestKingdomTracking(Base):
    """Tracks progress for kingdom quests."""

    __tablename__ = "quest_kingdom_tracking"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    quest_code = Column(
        String, ForeignKey("quest_kingdom_catalogue.quest_code"), primary_key=True
    )
    status = Column(String)
    progress = Column(Integer, default=0)
    progress_details = Column(JSONB, default={})
    ends_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    attempt_count = Column(Integer, default=1)
    started_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    objective_progress = Column(Integer, default=0)
    is_complete = Column(Boolean, default=False)


class RegionBonus(Base):
    """Bonus modifiers attached to specific world regions."""

    __tablename__ = "region_bonuses"

    region_code = Column(String, ForeignKey("region_catalogue.region_code"), primary_key=True)
    bonus_type = Column(String, primary_key=True)
    bonus_value = Column(Numeric)


class KingdomTemple(Base):
    __tablename__ = "kingdom_temples"

    temple_id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('kingdom_temples_temple_id_seq'::regclass)")
    )
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

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
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



class KingdomVillage(Base):
    __tablename__ = "kingdom_villages"

    village_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"))
    village_name = Column(Text, nullable=False)
    village_type = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KingdomVipStatus(Base):
    __tablename__ = "kingdom_vip_status"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    vip_level = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True))
    founder = Column(Boolean, default=False)

class TreatyNegotiationLog(Base):
    __tablename__ = "treaty_negotiation_log"

    log_id = Column(Integer, primary_key=True)
    treaty_id = Column(Integer, ForeignKey("alliance_treaties.treaty_id"))
    acting_alliance_id = Column(Integer)
    action = Column(Text)
    message = Column(Text)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class TreatyTerms(Base):
    __tablename__ = "treaty_terms"

    treaty_id = Column(Integer, ForeignKey("alliance_treaties.treaty_id"), primary_key=True)
    term_type = Column(Text, primary_key=True)
    value = Column(Text)


class TreatyTypeCatalogue(Base):
    __tablename__ = "treaty_type_catalogue"

    treaty_type = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)
    description = Column(Text)
    duration_days = Column(Integer, default=0)
    is_mutual = Column(Boolean, default=True)
    triggers_war_support = Column(Boolean, default=False)
    allows_cancelation = Column(Boolean, default=True)
    cancel_notice_days = Column(Integer, default=0)
    is_exclusive = Column(Boolean, default=False)
    treaty_group = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    join_wars = Column(Boolean, default=False)
    blocks_war = Column(Boolean, default=False)
    blocks_spy_ops = Column(Boolean, default=False)
    enables_shared_chat = Column(Boolean, default=False)
    enables_trade_bonus = Column(Boolean, default=False)
    auto_renew = Column(Boolean, default=False)
    exclusive_with = Column(ARRAY(Text), server_default=text("'{}'::text[]"))


class BuildingCatalogue(Base):
    __tablename__ = "building_catalogue"

    building_id = Column(Integer, primary_key=True, autoincrement=True)
    building_name = Column(Text, nullable=False)
    description = Column(Text)
    production_type = Column(Text)
    production_rate = Column(Integer)
    upkeep = Column(Integer)
    modifiers = Column(JSONB, server_default=text("'{}'::jsonb"))
    category = Column(Text)
    build_time_seconds = Column(Integer, server_default=text("3600"))
    prerequisites = Column(JSONB, server_default=text("'{}'::jsonb"))
    max_level = Column(Integer, server_default=text("10"))
    special_effects = Column(JSONB, server_default=text("'{}'::jsonb"))
    is_unique = Column(Boolean, server_default=text("false"))
    is_repeatable = Column(Boolean, server_default=text("true"))
    unlock_at_level = Column(Integer, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    cost_to_produce = Column(JSONB, server_default=text("'{}'::jsonb"))
    efficiency_multiplier = Column(Numeric, server_default=text("1.0"))
    wood_cost = Column(Integer, server_default=text("0"))
    stone_cost = Column(Integer, server_default=text("0"))
    iron_cost = Column(Integer, server_default=text("0"))
    gold_cost = Column(Integer, server_default=text("0"))
    wood_plan_cost = Column(Integer, server_default=text("0"))
    iron_ingot_cost = Column(Integer, server_default=text("0"))
    requires_tech_id = Column(Integer)
    build_time = Column(Integer, server_default=text("0"))
    effect_description = Column(Text)
    wood = Column(Integer, server_default=text("0"))
    stone = Column(Integer, server_default=text("0"))
    iron_ore = Column(Integer, server_default=text("0"))
    gold = Column(Integer, server_default=text("0"))
    gems = Column(Integer, server_default=text("0"))
    food = Column(Integer, server_default=text("0"))
    coal = Column(Integer, server_default=text("0"))
    livestock = Column(Integer, server_default=text("0"))
    clay = Column(Integer, server_default=text("0"))
    flax = Column(Integer, server_default=text("0"))
    tools = Column(Integer, server_default=text("0"))
    wood_planks = Column(Integer, server_default=text("0"))
    refined_stone = Column(Integer, server_default=text("0"))
    iron_ingots = Column(Integer, server_default=text("0"))
    charcoal = Column(Integer, server_default=text("0"))
    leather = Column(Integer, server_default=text("0"))
    arrows = Column(Integer, server_default=text("0"))
    swords = Column(Integer, server_default=text("0"))
    axes = Column(Integer, server_default=text("0"))
    shields = Column(Integer, server_default=text("0"))
    armour = Column(Integer, server_default=text("0"))
    wagon = Column(Integer, server_default=text("0"))
    siege_weapons = Column(Integer, server_default=text("0"))
    jewelry = Column(Integer, server_default=text("0"))
    spear = Column(Integer, server_default=text("0"))
    horses = Column(Integer, server_default=text("0"))
    pitchforks = Column(Integer, server_default=text("0"))


class BuildingCost(Base):
    __tablename__ = "building_costs"

    building_id = Column(Integer, ForeignKey("building_catalogue.building_id"), primary_key=True)
    resource_type = Column(Text, primary_key=True)
    amount = Column(Integer, nullable=False)


class AllianceSurrender(Base):
    """Records alliance surrender terms and status."""

    __tablename__ = "alliance_surrenders"

    surrender_id = Column(Integer, primary_key=True)
    alliance_war_id = Column(Integer, ForeignKey("alliance_wars.alliance_war_id"))
    surrendering_alliance_id = Column(Integer)
    accepted_by_alliance_id = Column(Integer)
    surrender_terms = Column(JSONB)
    status = Column(Text, default="pending")
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    peace_terms = Column(Text)
    gold_penalty = Column(Integer, default=0)


class AllianceTaxCollection(Base):
    """Log of resources taxed from alliance members."""

    __tablename__ = "alliance_tax_collections"

    collection_id = Column(BigInteger, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    resource_type = Column(Text, nullable=False)
    amount_collected = Column(BigInteger, default=0)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(Text)
    notes = Column(Text)


class AllianceTaxPolicy(Base):
    """Active tax rates for alliance resources."""

    __tablename__ = "alliance_tax_policies"

    alliance_id = Column(Integer, ForeignKey("alliances.alliance_id"), primary_key=True)
    resource_type = Column(Text, primary_key=True)
    tax_rate_percent = Column(Numeric, default=0)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))


class GlobalEventCondition(Base):
    """Conditions required for a global event."""

    __tablename__ = "global_event_conditions"

    event_id = Column(Integer, ForeignKey("global_events.event_id"), nullable=False)
    condition_type = Column(Text, nullable=False)
    condition_target = Column(Text)
    condition_value = Column(Text)


class GlobalEventEffect(Base):
    """Effects applied by a global event."""

    __tablename__ = "global_event_effects"

    event_id = Column(Integer, ForeignKey("global_events.event_id"), nullable=False)
    effect_type = Column(Text, nullable=False)
    target = Column(Text)
    magnitude = Column(Numeric)


class GlobalEventReward(Base):
    """Rewards granted upon global event completion."""

    __tablename__ = "global_event_rewards"

    event_id = Column(Integer, ForeignKey("global_events.event_id"), nullable=False)
    reward_type = Column(Text, nullable=False)
    reward_target = Column(Text)
    reward_amount = Column(Numeric, nullable=False)

class KingdomReligion(Base):
    """Religious affiliation and faith details for a kingdom."""

    __tablename__ = "kingdom_religion"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    religion_name = Column(Text)
    faith_level = Column(Integer, default=1)
    faith_points = Column(Integer, default=0)
    blessings = Column(JSONB, default=dict)
    blessing_1 = Column(Text)
    blessing_2 = Column(Text)
    blessing_3 = Column(Text)


class KingdomResearchTracking(Base):
    """Tracks research progress for a kingdom's technologies."""

    __tablename__ = "kingdom_research_tracking"

    kingdom_id = Column(Integer, ForeignKey("kingdoms.kingdom_id"), primary_key=True)
    tech_code = Column(String, ForeignKey("tech_catalogue.tech_code"), primary_key=True)
    status = Column(String)
    progress = Column(Integer, default=0)
    ends_at = Column(DateTime(timezone=True))





