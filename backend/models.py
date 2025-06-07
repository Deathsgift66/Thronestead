from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, DateTime, ForeignKey
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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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
