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



class Version(Base):
    __tablename__ = "version"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    region_name = Column(String, nullable=False)
    region_id = Column(Integer, nullable=False)
    version_name = Column(String, nullable=False)
    version_id = Column(Integer, nullable=False)

    regional_cities = Column(ARRAY(String), nullable=False)
    locations_ordered = Column(ARRAY(String), nullable=False)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
