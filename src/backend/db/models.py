import enum
from sqlalchemy import Column, Integer, String, Boolean, ARRAY, JSON, Enum, true
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
    UNKNOWN = "Unknown"

class AllPokemon(Base):
    __tablename__ = "all_pokemon"

    id = Column(Integer, nullable=False, autoincrement=True)
    poke_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    types = Column(ARRAY(String), nullable=False)
    past_types = Column(ARRAY(JSON), nullable=True)
    abilities = Column(ARRAY(String), nullable=False)
    weight = Column(Integer, nullable=False)
    base_hp = Column(Integer, nullable=False)
    base_attack = Column(Integer, nullable=False)
    base_defense = Column(Integer, nullable=False)
    base_special_attack = Column(Integer, nullable=False)
    base_special_defense = Column(Integer, nullable=False)
    base_speed = Column(Integer, nullable=False)
    evolution_data = Column(ARRAY(JSON), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


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
    caught_on = Column(String, nullable=True)
    evolution_data = Column(ARRAY(JSON), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    pokemon = relationship("AllPokemon")
    game_file = relationship("GameFiles", back_populates="owned_pokemon")


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    email = Column(String, nullable=True, unique=True)  # For OAuth users
    oauth_provider = Column(String, nullable=True)  # e.g., "google"
    oauth_provider_id = Column(String, nullable=True)  # OAuth provider's user ID

    # A user can have many game files
    game_files = relationship("GameFiles", back_populates="user")


class GameFiles(Base):
    __tablename__ = "game_files"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    trainer_name = Column(String, nullable=False)
    game_name = Column(String, nullable=False)
    starter_selected = Column(String, nullable=True)
    owned_pokemon = relationship("OwnedPokemon", back_populates="game_file", cascade="all, delete")
    gym_progress = Column(ARRAY(JSON), nullable=True)
    route_progress = Column(ARRAY(JSON), nullable=True)
    user = relationship("User", back_populates="game_files")

    # TODO: Last save

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
    region_name = Column(String, nullable=False)

    locations_ordered = Column(ARRAY(String), nullable=False)
    generation = relationship("Generation", back_populates="version")
    route = relationship("Route", back_populates="version")

class Route(Base):
    __tablename__ = "route"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # e.g. "Route 1"
    version_id = Column(Integer, ForeignKey("version.version_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("generation.region_id"), nullable=False)
    derives_from = Column(String, nullable=True)
    data = Column(JSON, nullable=False)

    generation = relationship("Generation", back_populates="route")
    version = relationship("Version", back_populates="route")


# derived from trainer_data.json
class Gym(Base):
    __tablename__ = "gym"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_name = Column(String, nullable=False)
    gym_number = Column(Integer, nullable=True)
    gym_path = Column(String, nullable=True)
    badge_path = Column(String, nullable=True)
    location = Column(String, nullable=False)
    trainer_name = Column(String, nullable=True)
    trainer_image = Column(String, nullable=False)
    badge_name =  Column(String, nullable=True)
    badge_type = Column(String, nullable=True)
    pokemon = Column(JSON, nullable=False)


class Trainer(Base):
    __tablename__ = "trainer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    generation = Column(Integer, nullable=False)
    game_names = Column(ARRAY(String), nullable=False)
    trainer_name = Column(String, nullable=False)
    trainer_image = Column(String, nullable=False)
    location = Column(String, nullable=False)
    route_id = Column(Integer, ForeignKey("route.id"), nullable=True)
    is_important = Column(Boolean, nullable=False, default=False)
    importance_reason = Column(String, nullable=True)
    starter_filter = Column(String, nullable=True)
    battle_order = Column(Integer, nullable=False)
    pokemon = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    route = relationship("Route")


class Type(Base):
    __tablename__ = "type"

    id = Column(Integer, primary_key=True)
    type_name = Column(String, nullable=False)
    generation_introduction = Column(Integer, nullable=False)
    current_damage_relations = Column(JSON, nullable=False)
    past_damage_relations = Column(JSON, nullable=True) # from generation_introduction to past_generation ex. (steel: gen 2 - 5 past damage relations, 6 - onwards current relations)


class Move(Base):
    __tablename__ = "move"

    id = Column(Integer, primary_key=True)            # PokeAPI move ID
    name = Column(String, nullable=False)              # e.g. "swords-dance"
    type_name = Column(String, nullable=False)         # e.g. "normal", "fire"
    power = Column(Integer, nullable=True)             # null for status moves
    pp = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=True)          # null for self-targeting
    damage_class = Column(String, nullable=False)      # "physical"/"special"/"status"
    effect = Column(String, nullable=True)             # English short_effect text
    generation = Column(Integer, nullable=False)       # Gen number (1-9)
    priority = Column(Integer, nullable=False, default=0)
