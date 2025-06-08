from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = 'users'
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

class PlayerMessage(Base):
    __tablename__ = 'player_messages'
    message_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    recipient_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)


class Alliance(Base):
    """Minimal alliance record used for foreign key relations."""

    __tablename__ = 'alliances'

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

    __tablename__ = 'alliance_members'

    alliance_id = Column(Integer, ForeignKey('alliances.alliance_id'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'), primary_key=True)
    username = Column(String)
    rank = Column(String)
    contribution = Column(Integer, default=0)
    status = Column(String)
    crest = Column(String)

class AllianceVault(Base):
    __tablename__ = 'alliance_vault'
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AllianceVaultTransactionLog(Base):
    __tablename__ = 'alliance_vault_transaction_log'
    transaction_id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey('alliances.alliance_id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    action = Column(String)
    resource_type = Column(String)
    amount = Column(BigInteger)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WarsTactical(Base):
    __tablename__ = 'wars_tactical'
    war_id = Column(Integer, primary_key=True)
    attacker_kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    defender_kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    phase = Column(String)
    castle_hp = Column(Integer, default=1000)
    battle_tick = Column(Integer, default=0)
    war_status = Column(String)


class UnitMovement(Base):
    __tablename__ = 'unit_movements'
    movement_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey('wars_tactical.war_id'))
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
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
    morale = Column(Integer)
    status = Column(String)
    visible_enemies = Column(JSONB, default={})


class CombatLog(Base):
    __tablename__ = 'combat_logs'
    combat_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey('wars_tactical.war_id'))
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
    __tablename__ = 'alliance_wars'
    alliance_war_id = Column(Integer, primary_key=True)
    attacker_alliance_id = Column(Integer, ForeignKey('alliances.alliance_id'))
    defender_alliance_id = Column(Integer, ForeignKey('alliances.alliance_id'))
    phase = Column(String)
    castle_hp = Column(Integer, default=10000)
    battle_tick = Column(Integer, default=0)
    war_status = Column(String)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))


class AllianceWarParticipant(Base):
    __tablename__ = 'alliance_war_participants'
    alliance_war_id = Column(Integer, ForeignKey('alliance_wars.alliance_war_id'), primary_key=True)
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'), primary_key=True)
    role = Column(String)


class AllianceWarCombatLog(Base):
    __tablename__ = 'alliance_war_combat_logs'
    combat_id = Column(Integer, primary_key=True)
    alliance_war_id = Column(Integer, ForeignKey('alliance_wars.alliance_war_id', ondelete='CASCADE'))
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
    __tablename__ = 'alliance_war_preplans'
    preplan_id = Column(Integer, primary_key=True)
    alliance_war_id = Column(Integer, ForeignKey('alliance_wars.alliance_war_id'))
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    preplan_jsonb = Column(JSONB)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AllianceWarScore(Base):
    __tablename__ = 'alliance_war_scores'
    alliance_war_id = Column(
        Integer,
        ForeignKey('alliance_wars.alliance_war_id', ondelete='CASCADE'),
        primary_key=True,
    )
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    victor = Column(String)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BattleResolutionLog(Base):
    __tablename__ = 'battle_resolution_logs'
    resolution_id = Column(Integer, primary_key=True)
    battle_type = Column(String)
    war_id = Column(Integer, ForeignKey('wars_tactical.war_id'))
    alliance_war_id = Column(Integer, ForeignKey('alliance_wars.alliance_war_id'))
    winner_side = Column(String)
    total_ticks = Column(Integer, default=0)
    attacker_casualties = Column(Integer, default=0)
    defender_casualties = Column(Integer, default=0)
    loot_summary = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WarScore(Base):
    __tablename__ = 'war_scores'
    war_id = Column(Integer, ForeignKey('wars_tactical.war_id'), primary_key=True)
    attacker_score = Column(Integer, default=0)
    defender_score = Column(Integer, default=0)
    victor = Column(String)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TerrainMap(Base):
    __tablename__ = 'terrain_map'
    terrain_id = Column(Integer, primary_key=True)
    war_id = Column(Integer, ForeignKey('wars_tactical.war_id'))
    tile_map = Column(JSONB)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())


class UnitStat(Base):
    __tablename__ = 'unit_stats'
    unit_type = Column(String, primary_key=True)
    tier = Column(Integer)
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
    __tablename__ = 'kingdom_troops'
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'), primary_key=True)
    unit_type = Column(String, ForeignKey('unit_stats.unit_type'), primary_key=True)
    quantity = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Notification(Base):
    """Player notifications."""

    __tablename__ = 'notifications'

    notification_id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    title = Column(String)
    message = Column(Text)
    category = Column(String)
    priority = Column(String)
    link_action = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)


class BlackMarketListing(Base):
    """Active player listings on the Black Market."""

    __tablename__ = 'black_market_listings'

    listing_id = Column(Integer, primary_key=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    item = Column(String)
    price = Column(Numeric)
    quantity = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GameSetting(Base):
    __tablename__ = 'game_settings'

    setting_key = Column(String, primary_key=True)
    setting_value = Column(JSONB)
    setting_type = Column(String)
    description = Column(Text)
    default_value = Column(JSONB)
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))


class KingdomHistoryLog(Base):
    """Chronological history of important events for kingdoms."""

    __tablename__ = 'kingdom_history_log'

    log_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    event_type = Column(String)
    event_details = Column(Text)
    event_date = Column(DateTime(timezone=True), server_default=func.now())
