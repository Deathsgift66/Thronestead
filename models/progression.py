from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from backend.database import Base


class KingdomCastleProgression(Base):
    """Tracks castle progression level and experience for each kingdom."""

    __tablename__ = 'kingdom_castle_progression'

    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'), primary_key=True)
    castle_level = Column(Integer, default=1)
    castle_xp = Column(Integer, default=0)
    xp_for_next = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class KingdomNoble(Base):
    """Represents nobles serving a kingdom."""

    __tablename__ = 'kingdom_nobles'

    noble_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    name = Column(String)
    title = Column(String)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    loyalty = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KingdomKnight(Base):
    """Represents knights available to a kingdom."""

    __tablename__ = 'kingdom_knights'

    knight_id = Column(Integer, primary_key=True)
    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'))
    name = Column(String)
    rank = Column(String)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TroopSlots(Base):
    """Slot tracking including bonuses from castle, nobles, and knights."""

    __tablename__ = 'kingdom_troop_slots'

    kingdom_id = Column(Integer, ForeignKey('kingdoms.kingdom_id'), primary_key=True)
    base_slots = Column(Integer, default=20)
    used_slots = Column(Integer, default=0)
    morale = Column(Integer, default=100)
    castle_bonus = Column(Integer, default=0)
    noble_bonus = Column(Integer, default=0)
    knight_bonus = Column(Integer, default=0)
