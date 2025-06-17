# Project Name: Thronestead©
# File Name: progression.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.db_base import Base


class KingdomCastleProgression(Base):
    """
    Tracks the level progression of a kingdom's castle.
    """

    __tablename__ = 'kingdom_castle_progression'

    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'), primary_key=True)
    castle_level = Column(Integer, default=1)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KingdomNoble(Base):
    """
    Represents a noble who serves the kingdom. Nobles may influence production, diplomacy, or faith.
    Can be assigned to villages for specific bonuses. Loyalty affects output.
    """

    __tablename__ = 'kingdom_nobles'

    noble_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    noble_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    level = Column(Integer, default=1)
    loyalty = Column(Integer, default=50)  # Ranges from 0 to 100
    specialization = Column(String, default='general')  # e.g., 'economy', 'war', 'faith'
    assigned_village_id = Column(Integer, ForeignKey('kingdom_villages.village_id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KingdomKnight(Base):
    """
    Represents a knight hero in the kingdom. Knights impact troop morale and battlefield performance.
    Future-proofed with leadership stats and morale aura.
    """

    __tablename__ = 'kingdom_knights'

    knight_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    knight_name = Column(String, nullable=False)
    rank = Column(String, default='Squire')  # e.g., 'Squire', 'Knight', 'Champion', 'Paladin'
    level = Column(Integer, default=1)
    leadership = Column(Integer, default=10)  # Affects morale bonus
    tactics = Column(Integer, default=10)     # Influences war utility
    morale_aura = Column(Integer, default=0)  # % boost to nearby troops
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TroopSlots(Base):
    """
    Tracks the total and used troop slots for a kingdom.
    Bonuses from buildings, tech, nobles, and knights are factored in.
    Also tracks morale and cooldown from recent combat.
    """

    __tablename__ = 'kingdom_troop_slots'

    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'), primary_key=True)
    base_slots = Column(Integer, default=20)
    used_slots = Column(Integer, default=0)
    morale = Column(Integer, default=100)  # Base morale; affected by war losses, knights, tech, etc.
    slots_from_buildings = Column(Integer, default=0)
    slots_from_tech = Column(Integer, default=0)
    slots_from_projects = Column(Integer, default=0)
    slots_from_events = Column(Integer, default=0)
    morale_bonus_buildings = Column(Integer, default=0)
    morale_bonus_tech = Column(Integer, default=0)
    morale_bonus_events = Column(Integer, default=0)
    last_morale_update = Column(DateTime(timezone=True), server_default=func.now())
    morale_cooldown_seconds = Column(Integer, default=0)
    last_in_combat_at = Column(DateTime(timezone=True), nullable=True)
    currently_in_combat = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
