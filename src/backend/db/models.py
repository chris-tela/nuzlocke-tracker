from sqlalchemy import Column, Integer, String, Boolean, ARRAY, JSON
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from .database import Base

class AllPokemon(Base):
    __tablename__ = "all_pokemon"

    id = Column(Integer, nullable=False, autoincrement=True)
    poke_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    types = Column(ARRAY(String), nullable=False)
    abilities = Column(ARRAY(String), nullable=False)
    weight = Column(Integer, nullable=False)
    base_hp = Column(Integer, nullable=False)
    base_attack = Column(Integer, nullable=False)
    base_defense = Column(Integer, nullable=False)
    base_special_attack = Column(Integer, nullable=False)
    base_special_defense = Column(Integer, nullable=False)
    base_speed = Column(Integer, nullable=False)
    sprite = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    party_pokemon = relationship("PartyPokemon", back_populates="pokemon")

class PartyPokemon(Base):
    __tablename__ = "party_pokemon"

    id = Column(Integer, primary_key=True, nullable=False)
    poke_id = Column(Integer, ForeignKey("all_pokemon.poke_id", ondelete="SET NULL"), nullable=False)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    nature = Column(String, nullable=False)
    ability = Column(String, nullable=False)
    types = Column(ARRAY(String), nullable=False)
    level = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    gender = Column(String, nullable=True)
    evolution_data = Column(ARRAY(JSON), nullable=True)
    sprite = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    pokemon = relationship("AllPokemon", back_populates="party_pokemon")


class Region(Base):
    __tablename__ = "region"

    region_id = Column(Integer, primary_key=True, nullable=False, unique=True)
    region_name = Column(String, nullable=False)
    regional_cities = Column(ARRAY(String), nullable=False)

    versions = relationship("Version", back_populates="region")
    routes = relationship("Route", back_populates="region")

class Version(Base):
    __tablename__ = "version"

    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=False)
    version_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    version_name = Column(String, nullable=False)


    locations_ordered = Column(ARRAY(String), nullable=False)
    region = relationship("Region", back_populates="versions")
    routes = relationship("Route", back_populates="version")

class Route(Base):
    __tablename__ = "route"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # e.g. "Route 1"
    version_id = Column(Integer, ForeignKey("version.version_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=False)
    data = Column(JSON, nullable=False)

    region = relationship("Region", back_populates="routes")
    version = relationship("Version", back_populates="routes")


