import enum
from sqlalchemy import Column, Integer, String, Boolean, ARRAY, JSON, Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from .database import Base

class Nature(enum.Enum):
    HARDY = "Hardy"
    LONELY = "Lonely"
    BRAVE = "Brave"
    ADAMANT = "Adamant"
    NAUGHTY = "Naughty"
    BOLD = "Bold"
    DOCILE = "Docile"
    RELAXED = "Relaxed"
    IMPISH = "Impish"
    LAX = "Lax"
    TIMID = "Timid"
    HASTY = "Hasty"
    SERIOUS = "Serious"
    JOLLY = "Jolly"
    NAIVE = "Naive"
    MODEST = "Modest"
    MILD = "Mild"
    QUIET = "Quiet"
    BASHFUL = "Bashful"
    RASH = "Rash"
    CALM = "Calm"
    GENTLE = "Gentle"
    SASSY = "Sassy"
    CAREFUL = "Careful"
    QUIRKY = "Quirky"    

class Status(enum.Enum):
    PARTY = "Party"
    STORED = "Stored"
    FAINTED = "Fainted"

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
    evolution_data = Column(ARRAY(JSON), nullable=True)
    sprite = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class PartyPokemon(Base):
    __tablename__ = "party_pokemon"

    id = Column(Integer, primary_key=True, nullable=False)
    game_file_id = Column(Integer, ForeignKey("game_files.id", ondelete="CASCADE"), nullable=False)

    # Foreign key to the OwnedPokemon entry that this represents
    owned_pokemon_id = Column(Integer, ForeignKey("owned_pokemon.id", ondelete="CASCADE"), nullable=False)

    owned_pokemon = relationship("OwnedPokemon", back_populates="party_entry")
    game_file = relationship("GameFiles", back_populates="party_pokemon")


class OwnedPokemon(Base):
    __tablename__ = "owned_pokemon"

    id = Column(Integer, primary_key=True, nullable=False)
    game_file_id = Column(Integer, ForeignKey("game_files.id", ondelete="CASCADE"), nullable=False)

    poke_id = Column(Integer, ForeignKey("all_pokemon.poke_id", ondelete="SET NULL"), nullable=False)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    nature = Column(Enum(Nature), nullable=True)
    ability = Column(String, nullable=True)
    types = Column(ARRAY(String), nullable=False)
    level = Column(Integer, nullable=False)
    gender = Column(String, nullable=True)
    status = Column(Enum(Status), nullable=False)
    evolution_data = Column(ARRAY(JSON), nullable=True)
    sprite = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    pokemon = relationship("AllPokemon")
    party_entry = relationship("PartyPokemon", back_populates="owned_pokemon", uselist=False)
    game_file = relationship("GameFiles", back_populates="owned_pokemon")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False, unique=True)

    # A user can have many game files
    game_files = relationship("GameFiles", back_populates="user")


class GameFiles(Base):
    __tablename__ = "game_files"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    trainer_name = Column(String, nullable=False)
    game_name = Column(String, nullable=False)
    party_pokemon = relationship("PartyPokemon", back_populates="game_file", cascade="all, delete")
    owned_pokemon = relationship("OwnedPokemon", back_populates="game_file", cascade="all, delete")
    gym_progress = Column(ARRAY(JSON), nullable=True)
    route_progress = Column(ARRAY(JSON), nullable=True)
    user = relationship("User", back_populates="game_files")



class Generation(Base):
    __tablename__ = "generation"

    generation_id = Column(Integer, primary_key=True, nullable=False, unique=True)

    pokemon = Column(ARRAY(String), nullable=False)

    region_id = Column(Integer, unique=True, nullable=False)
    region_name = Column(String, nullable=False)
    regional_cities = Column(ARRAY(String), nullable=False)

    version_groups = Column(ARRAY(String), nullable=False)
    version = relationship("Version", back_populates="generation")
    route = relationship("Route", back_populates="generation")





class Version(Base):
    __tablename__ = "version"

    generation_id = Column(Integer, ForeignKey("generation.generation_id"), nullable=False)
    version_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    version_name = Column(String, nullable=False)


    locations_ordered = Column(ARRAY(String), nullable=False)
    generation = relationship("Generation", back_populates="version")
    route = relationship("Route", back_populates="version")

class Route(Base):
    __tablename__ = "route"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # e.g. "Route 1"
    version_id = Column(Integer, ForeignKey("version.version_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("generation.region_id"), nullable=False)
    data = Column(JSON, nullable=False)

    generation = relationship("Generation", back_populates="route")
    version = relationship("Version", back_populates="route")


