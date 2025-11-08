# used to simulate the web app's core logic in the terminal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from db import database
from db import models
from sqlalchemy.orm import Session
from typing import cast
from fastapi import Depends


def main():

    print("Welcome to the Pokemon CLI!")
    print("What game are you playing?")

    selected_game = game()

    print(f"You are playing {selected_game} Version")
    print("What is your trainer name?")
    trainer_name = input()
    print(f"Welcome, {trainer_name}! Let's get started.")
    print("What is your starter pokemon?")
    starter(selected_game)




def game() -> str:
    while True:
        game = input()

        match game:
            case "black":
                break
            case "white":
                break
            case "black-2":
                break
            case "white-2":
                break
            case "red":
                break
            case _:
                print("Invalid game")
    return game

def starter(game: str, db: Session = Depends(database.get_db)):
    db = database.SessionLocal()
    try:
        version = db.query(models.Version).filter(models.Version.version_name == game).first()
        if version:
            gen = db.query(models.Generation).filter(models.Generation.generation_id == version.generation_id).first()

            if gen:
                pokedex = gen.pokemon
                # gen5 pokedex starts with victini, which breaks the pattern of pokedexes starting with starter pokemons
                generation_id = cast(int, gen.generation_id)
                if generation_id == 5:
                    starters = pokedex[1:4]
                else:
                    starters = pokedex[0:3]

                print(starters)
                while True:
                    starter_selected = input().lower()
                    if starter_selected in starters:
                        break
                
                # search for starter in all_pokemon db

                starter_data = db.query(models.AllPokemon).filter(models.AllPokemon.name == starter_selected).first()

                if starter_data:
                    added_pokemon = add_to_party(starter_data)
                    add_to_party_database(added_pokemon, db)



                return starters
        print("error :(")
    finally:
        db.close()


def add_to_party(pokemon_data):

    if pokemon_data: 
        poke_id = pokemon_data.poke_id
        name = pokemon_data.name
        types = pokemon_data.types
        abilities = pokemon_data.abilities
        sprite = pokemon_data.sprite
        evolution_data = pokemon_data.evolution_data

    print("It's gender? (m or f):")
    while True:
        gender = input().lower()
        if(gender == "m" or gender == "f"):
            break
    
    print("Does it have a nickname? (y = yes): ")

    nickname_input = input().lower()
    if(nickname_input == "y"):
        print("Nickname: ")
        nickname = input().lower()
    else:
        nickname = ""

    print("It's nature?:")
    nature = input().lower()    

    print("It's ability?")
    print(abilities)
    while True:
        ability = input().lower()
        if(abilities.__contains__(ability)):
            break
    
    created_at = datetime.now()

    added_pokemon = models.PartyPokemon(
        poke_id = poke_id,
        name = name,
        nickname = nickname,
        nature = nature,
        ability = ability,
        types = types,
        level = 5,
        gender = gender,
        evolution_data = evolution_data,
        sprite = sprite,
        created_at = created_at
    )

    return added_pokemon

def add_to_party_database(added_pokemon, db: Session = Depends(database.get_db)):
    db.add(added_pokemon)
    db.commit()
    db.close()
    print("added to party!")


if __name__ == "__main__":
    main()

