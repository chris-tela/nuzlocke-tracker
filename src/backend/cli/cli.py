# used to simulate the web app's core logic in the terminal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import database
from db import models
from sqlalchemy.orm import Session

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

def starter(game: str):
    db = database.SessionLocal()
    try:
        version = db.query(models.Version).filter(models.Version.version_name == game).first()
        if version:
            gen = db.query(models.Generation).filter(models.Generation.generation_id == version.generation_id).first()

            if gen:
                pokedex = gen.pokemon
                # gen5 pokedex starts with victini, which breaks the pattern of pokedexes starting with starter pokemons
                if gen.generation_id == 5:
                    starters = pokedex[1:4]
                else:
                    starters = pokedex[0:3]

                print(starters)
                while True:
                    starter_selected = input().lower()
                    if starters.__contains__(starter_selected):
                        break
                
                # search for starter in all_pokemon db

                starter_data = db.query(models.AllPokemon).filter(models.AllPokemon.name == starter_selected).first()

                if starter_data:
                    poke_id = starter_data.poke_id
                    types = starter_data.types
                    abilities = starter_data.abilities
                    sprite = starter_data.sprite
                    evolution_data = starter_data.evolution_data

                return starters
        print("error :(")
    finally:
        db.close()


if __name__ == "__main__":
    main()

