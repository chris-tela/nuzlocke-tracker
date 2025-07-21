from sqlalchemy import Column, Integer, String, Boolean, List, Dict
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from database import Base

class AllPokemon(Base):
    __tablename__ = "all_pokemon"

    id = Column(Integer, primary_key=True, nullable=False)
    poke_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(List[String], nullable=False)
    abilities = Column(List[String], nullable=False)
    weight = Column(Integer, nullable=False)
    base_hp = Column(Integer, nullable=False)
    base_attack = Column(Integer, nullable=False)
    base_defense = Column(Integer, nullable=False)
    base_special_attack = Column(Integer, nullable=False)
    base_special_defense = Column(Integer, nullable=False)
    base_speed = Column(Integer, nullable=False)
    sprite = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class PartyPokemon(Base):
    __tablename__ = "party_pokemon"

    id = Column(Integer, primary_key=True, nullable=False)
    poke_id = Column(Integer, ForeignKey("all_pokemon.poke_id", ondelete="SET NULL"), nullable=False)
    name = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    nature = Column(String, nullable=False)
    ability = Column(String, nullable=False)
    types = Column(List[String], nullable=False)
    level = Column(Integer, nullable=False)
    weight = Column(Integer, nullable=False)
    gender = Column(String, nullable=True)
    evolution_data = Column(List[Dict[Dict[str, str]]], nullable=True)
    sprite = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    pokemon = relationship("AllPokemon", back_populates="party_pokemon")

