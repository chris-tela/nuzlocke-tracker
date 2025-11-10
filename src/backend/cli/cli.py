# used to simulate the web app's core logic in the terminal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json
from db import database
from db import models
from sqlalchemy.orm import Session
from typing import cast, Optional

trainer_data = []

route_progression = []
gym_progression = []

def main():

    print("Welcome to the Pokemon CLI!")
    print("What game are you playing?")

    selected_game = game_choice()

    print(f"You are playing {selected_game} Version")
    print("What is your trainer name?")
    trainer_name = input()
    print(f"Welcome, {trainer_name}! Let's get started.")
    print("What is your starter pokemon?")
    trainer_data.append(selected_game)
    trainer_data.append(trainer_name)
    starter(selected_game)


    game()



def game_choice() -> str:
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
                    add_to_party_database(added_pokemon)

                save_to_storage()
                return

        print("error :(")
    finally:
        db.close()

# main gameplay
def game():
    while True:
        print("------------------------")
        print("Select '1' to view & update team")
        print("Select '2' to view & update upcoming routes/encounter locations")
        print("Select '3' to view & update upcoming gym locations")
        print("Select '4' to save data and exit!")
        print("------------------------")

        selection = input().lower()
        if(selection == "1"):
            team()
        if(selection == "2"):
            encounters()
        if(selection == "4"):
            save_to_storage()
        
        

def team():


    db = database.SessionLocal()

    print("Team Status:")
    party_pokemon_list = db.query(models.PartyPokemon).all()


    if party_pokemon_list:
        for pokemon in party_pokemon_list:
            print("Pokemon: " + pokemon.name)
            print("Nickname: " + pokemon.nickname)
            print("Level: " + str(pokemon.level))
            print("Type(s): " + str(pokemon.types))
            print("-----------\n")

        print("Would you like to edit any information of a pokemon?: (y = yes)")
        edit = input().lower()
        if(edit == "y"):
            edit_pokemon(party_pokemon_list, db)
    else:
        print("Team is empty!")



def edit_pokemon(party_pokemon_list, db):
    print("Which pokemon would you like to edit?: ")

    party_pokemon = db.query(models.PartyPokemon).all()
    i = 1
    for pokemon in party_pokemon:
        print(str(i) + ": " + pokemon.name)
        i += 1 
    

    choice = int(input().lower())
    poke_data = party_pokemon[choice - 1] 
        
    print("Would you like to: ")
    print("1: Change Level: ")
    print("2: Edit name: ")
    choice = input().lower()
    if(choice == "1"):
        print("Current level is: " + str(poke_data.level))
        print("What level would you like to be?: ")
        level = int(input().lower())
        if(level <= 100 and level >= 1):
            # db update pokemon level
            poke_data.level = level

            if(poke_data.level >= int(poke_data.evolution_data[0]["evolves_to"]["evolution_details"][0]["min_level"])):
                print("Would you like to evolve your pokemon?")
                choice = input().lower()
                if(choice == "y"):
                    evolved_pokemon_name = poke_data.evolution_data[0]["evolves_to"]["species"]
                    evolved_pokemon_data = db.query(models.AllPokemon).filter(models.AllPokemon.name == evolved_pokemon_name).first()
                    if evolved_pokemon_data:
                        evolve(poke_data, evolved_pokemon_data, db)

            else:
                db.commit()
            print(f"Pokemon level updated to {level}!")
        else:
            print("Invalid level. Level must be between 1 and 100.")
# replace pokemon with it's evolved form
def evolve(old_pokemon, new_pokemon, db):
    """
    Evolve a pokemon to its evolved form.
    Keeps: nickname, nature, level, gender, created_at (automatically preserved)
    Updates: poke_id, name, types, sprite, evolution_data, ability (user selects)
    """
    # Update from new pokemon data
    old_pokemon.poke_id = new_pokemon.poke_id
    old_pokemon.name = new_pokemon.name
    old_pokemon.types = new_pokemon.types
    old_pokemon.sprite = new_pokemon.sprite
    old_pokemon.evolution_data = new_pokemon.evolution_data
    
    # Ask user to select new ability
    print(f"Your pokemon can have these abilities:")
    print(new_pokemon.abilities)
    print("Which ability would you like?")
    while True:
        ability_input = input().lower()
        # Find the matching ability with original casing
        matching_ability = None
        for ab in new_pokemon.abilities:
            if ab.lower() == ability_input:
                matching_ability = ab
                break
        if matching_ability:
            old_pokemon.ability = matching_ability
            break
        else:
            print("Invalid ability. Please choose from the list above.")
    
    # Commit changes to database
    db.commit()
    print(f"Congratulations! Your pokemon evolved into {old_pokemon.name}!")
    
def encounters():
    """
    Display routes/encounters for the current game and allow user to update route progression.
    Reads game name from storage.json to query routes from database.
    """
    # Read storage.json to get game name
    storage_path = os.path.join(os.path.dirname(__file__), "storage.json")
    game_name = ""
    
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            storage_data = json.load(f)
            game_name = storage_data.get("trainer_data", {}).get("game_name", "")
    except FileNotFoundError:
        print("Storage file not found. Using trainer_data global variable.")
        if len(trainer_data) > 0:
            game_name = trainer_data[0]
    
    if not game_name:
        print("No game name found. Please start a new game first.")
        return
    
    db = database.SessionLocal()
    try:
        # Query version by game name
        version = db.query(models.Version).filter(models.Version.version_name == game_name).first()
        if not version:
            print(f"Version '{game_name}' not found in database.")
            return
        
        # Get all routes for this version
        routes = db.query(models.Route).filter(models.Route.version_id == version.version_id).all()
        
        if not routes:
            print(f"No routes found for {game_name}.")
            return
        
        print(f"\n=== Routes and Encounters for {game_name} ===\n")
        
        # Display routes and their encounters
        for i, route in enumerate(routes, 1):
            print(f"{i}. {route.name}")
            print(f"   Encounters:")
            
            # Route.data contains encounter data: [name, min_level, max_level, version_name, region_name, encounter_method]
            if route.data:
                for encounter in route.data:
                    pokemon_name = encounter[0] if len(encounter) > 0 else "Unknown"
                    min_level = encounter[1] if len(encounter) > 1 else "?"
                    max_level = encounter[2] if len(encounter) > 2 else "?"
                    methods = encounter[5] if len(encounter) > 5 else []
                    methods_str = ", ".join(methods) if methods else "walk"
                    print(f"      - {pokemon_name} (Lv. {min_level}-{max_level}) [{methods_str}]")
            print()
        
        # Allow user to update route progression
        print("Would you like to update route progression? (y = yes)")
        update_choice = input().lower()
        if update_choice == "y":
            print("Which route would you like to update? (Enter route number)")
            try:
                route_choice = int(input())
                if 1 <= route_choice <= len(routes):
                    selected_route = routes[route_choice - 1]
                    update_route_progression(selected_route, db)
                else:
                    print("Invalid route number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    except Exception as e:
        print(f"Error loading encounters: {e}")
        raise
    finally:
        db.close()

def update_route_progression(route, db):
    """
    Update route progression - mark route as caught and record which pokemon was caught.
    """
    print(f"\nUpdating progression for {route.name}")
    print("Have you caught a pokemon on this route? (y = yes)")
    caught_choice = input().lower()
    
    if caught_choice == "y":
        # Show available pokemon for this route
        if route.data:
            print("Which pokemon did you catch?")
            pokemon_list = [encounter[0] for encounter in route.data if len(encounter) > 0]
            for i, pokemon in enumerate(pokemon_list, 1):
                print(f"  {i}. {pokemon}")
            
            try:
                pokemon_choice = int(input())
                if 1 <= pokemon_choice <= len(pokemon_list):
                    caught_pokemon = pokemon_list[pokemon_choice - 1]
                    
                    # Update route_progression global variable
                    route_entry = {
                        "route": route.name,
                        "caught": True,
                        "pokemon_name": caught_pokemon
                    }
                    
                    # Check if route already exists in route_progression
                    route_exists = False
                    for i, existing_route in enumerate(route_progression):
                        if existing_route.get("route") == route.name:
                            route_progression[i] = route_entry
                            route_exists = True
                            break
                    
                    if not route_exists:
                        route_progression.append(route_entry)
                    
                    print(f"Route progression updated: {route.name} - Caught {caught_pokemon}")
                else:
                    print("Invalid pokemon choice.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        else:
            print("No encounter data available for this route.")
    else:
        # Mark route as not caught
        route_entry = {
            "route": route.name,
            "caught": False,
            "pokemon_name": None
        }
        
        # Check if route already exists in route_progression
        route_exists = False
        for i, existing_route in enumerate(route_progression):
            if existing_route.get("route") == route.name:
                route_progression[i] = route_entry
                route_exists = True
                break
        
        if not route_exists:
            route_progression.append(route_entry)
        
        print(f"Route progression updated: {route.name} - Not caught")
def save_to_storage():
    """
    Save game progress to storage.json in the format specified above.
    Gets party pokemon from DB and formats all data according to the JSON structure.
    """
    db = database.SessionLocal()
    try:
        # Get all party pokemon from database
        party_pokemon_list = db.query(models.PartyPokemon).all()
        
        # Convert party pokemon to dictionary format with all fields
        party_pokemon_json = []
        for pokemon in party_pokemon_list:
            # Handle datetime serialization
            created_at_str = None
            if pokemon.created_at is not None:
                if isinstance(pokemon.created_at, datetime):
                    created_at_str = pokemon.created_at.isoformat()
                else:
                    created_at_str = str(pokemon.created_at)
            
            pokemon_dict = {
                "id": pokemon.id,
                "poke_id": pokemon.poke_id,
                "name": pokemon.name,
                "nickname": pokemon.nickname,
                "nature": pokemon.nature,
                "ability": pokemon.ability,
                "types": pokemon.types,
                "level": pokemon.level,
                "gender": pokemon.gender,
                "evolution_data": pokemon.evolution_data,
                "sprite": pokemon.sprite,
                "created_at": created_at_str
            }
            party_pokemon_json.append(pokemon_dict)
        
        # Format trainer_data from global variable or use defaults
        trainer_name = trainer_data[1] if len(trainer_data) > 1 else ""
        game_name = trainer_data[0] if len(trainer_data) > 0 else ""
        
        trainer_data_json = {
            "trainer_name": trainer_name,
            "game_name": game_name
        }
        
        # Format gym_progression - convert list to dict if needed, or use as-is
        gym_progression_json = {}
        if isinstance(gym_progression, list):
            # If it's a list, convert to dict format
            for i, passed in enumerate(gym_progression, 1):
                gym_progression_json[f"gym_{i}"] = passed
        elif isinstance(gym_progression, dict):
            gym_progression_json = gym_progression
        else:
            # Default empty dict
            gym_progression_json = {}
        
        # Format route_progression - use the array format as specified
        route_progression_json = route_progression if isinstance(route_progression, list) else []
        
        # Build the complete gamefile structure
        gamefile = {
            "trainer_data": trainer_data_json,
            "party_pokemon": party_pokemon_json,
            "gym_progression": gym_progression_json,
            "route_progression": route_progression_json
        }
        
        # Save to storage.json
        storage_path = os.path.join(os.path.dirname(__file__), "storage.json")
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(gamefile, f, indent=2, ensure_ascii=False)
        
        print(f"Game data saved to {storage_path}")
        return gamefile
        
    except Exception as e:
        print(f"Error saving to storage: {e}")
        raise
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



def add_to_party_database(added_pokemon):
    db = database.SessionLocal()
    try:
        db.add(added_pokemon)
        db.commit()
        print("added to party!")
    except Exception as e:
        db.rollback()
        print(f"Error adding pokemon to database: {e}")
        raise
    finally:
        db.close()



if __name__ == "__main__":
    game()

