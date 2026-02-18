"""Pydantic data models for Pokemon save file structures."""

from __future__ import annotations

from pydantic import BaseModel


class Move(BaseModel):
    """A single move known by a Pokemon."""

    name: str
    pp: int
    pp_max: int | None = None


class Stats(BaseModel):
    """Computed battle stats (party Pokemon only)."""

    hp: int
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int


class EVs(BaseModel):
    """Effort Values (or Stat Experience for Gen 1-2).

    Gen 1-2: values range 0-65535 (16-bit "stat experience").
    Gen 3+:  values range 0-255 (8-bit EVs), 510 total cap.
    """

    hp: int
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int


class IVs(BaseModel):
    """Individual Values (or Determinant Values for Gen 1-2).

    Gen 1-2: values range 0-15 (4-bit DVs). HP is derived from other DVs.
    Gen 3+:  values range 0-31 (5-bit IVs packed into a u32).
    """

    hp: int
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int


class Playtime(BaseModel):
    """In-game playtime counter."""

    hours: int
    minutes: int
    seconds: int


class Item(BaseModel):
    """An item in the bag or held by a Pokemon."""

    name: str
    quantity: int


class Pokemon(BaseModel):
    """A single Pokemon, either in the party or a PC box.

    Fields that do not exist in older generations are set to None.
    For example, held_item is None in Gen 1, ability is None in Gen 1-2, etc.
    """

    species: str
    species_id: int
    nickname: str | None = None
    level: int
    moves: list[Move]
    hp: int | None = None
    max_hp: int | None = None
    stats: Stats | None = None
    evs: EVs
    ivs: IVs
    held_item: str | None = None
    ability: str | None = None
    nature: str | None = None
    friendship: int | None = None
    ot_name: str
    ot_id: int
    met_location: str | None = None
    met_level: int | None = None
    pokeball: str | None = None
    pokerus: bool = False
    is_shiny: bool = False
    is_egg: bool = False
    location: str = "party"


class Trainer(BaseModel):
    """Trainer profile data extracted from the save file."""

    name: str
    id: int
    secret_id: int | None = None
    gender: str | None = None
    money: int
    badges: list[str]
    playtime: Playtime
    pokedex_owned: int
    pokedex_seen: int


class SaveFile(BaseModel):
    """Top-level model representing an entire parsed save file."""

    generation: int
    game: str
    trainer: Trainer
    party: list[Pokemon]
    boxes: dict[str, list[Pokemon]]
    bag: dict[str, list[Item]]
