# used to simulate the web app's core logic in the terminal
from ast import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import json
from db import database
from db import models
from sqlalchemy.orm import Session
from typing import NoReturn, cast, Optional

trainer_data = []

route_progression = []
gym_progression = []

# Global variables to track current session
current_user: Optional[models.User] = None
current_game_file: Optional[models.GameFiles] = None

def main():
    global current_user, current_game_file
    
    print("Welcome to the Pokemon CLI!")
    
    # Account management
    current_user = select_or_create_user()
    if not current_user:
        print("Failed to select or create user. Exiting.")
        return
    
    # Game file management
    current_game_file = select_or_create_game_file(current_user)
    if not current_game_file:
        print("Failed to select or create game file. Exiting.")
        return
    
    print(f"\nWelcome back, {current_user.username}!")
    print(f"Playing {current_game_file.game_name} as {current_game_file.trainer_name}")
    print("Let's get started!\n")
    
    # Check if this is a new game file (no pokemon yet)
    db = database.SessionLocal()
    try:
        existing_pokemon = db.query(models.OwnedPokemon).filter(
            models.OwnedPokemon.game_file_id == current_game_file.id
        ).first()
        
        if not existing_pokemon:
            print("What is your starter pokemon?")
            # Access actual values from the model instance
            game_name_value = getattr(current_game_file, 'game_name', '')
            game_file_id_value = getattr(current_game_file, 'id', 0)
            starter(str(game_name_value), int(game_file_id_value))
    finally:
        db.close()
    
    # Update trainer_data for compatibility with existing code
    trainer_data.clear()
    trainer_data.append(str(current_game_file.game_name))
    trainer_data.append(str(current_game_file.trainer_name))
    
    game()



def create_account() -> Optional[models.User]:
    """Create a new user account."""
    db = database.SessionLocal()
    try:
        print("Enter a username for your new account:")
        while True:
            username = input().strip()
            if not username:
                print("Username cannot be empty. Please try again:")
                continue
            
            # Check if username already exists
            existing_user = db.query(models.User).filter(models.User.username == username).first()
            if existing_user:
                print(f"Username '{username}' already exists. Please choose a different username:")
                continue
            
            # Create new user
            new_user = models.User(username=username)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            print(f"Account '{username}' created successfully!")
            return new_user
    except Exception as e:
        db.rollback()
        print(f"Error creating account: {e}")
        return None
    finally:
        db.close()

def select_user() -> Optional[models.User]:
    """Select an existing user from the database."""
    db = database.SessionLocal()
    try:
        users = db.query(models.User).all()
        
        if not users:
            print("No users found in database.")
            return None
        
        print("\nSelect a user:")
        for i, user in enumerate(users, 1):
            game_count = len(user.game_files) if user.game_files else 0
            print(f"{i}. {user.username} ({game_count} game file(s))")
        
        while True:
            try:
                choice = input("\nEnter the number of the user (or '0' to go back): ").strip()
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(users):
                    selected_user = users[choice_num - 1]
                    db.refresh(selected_user)
                    return selected_user
                else:
                    print(f"Please enter a number between 1 and {len(users)}:")
            except ValueError:
                print("Please enter a valid number:")
    except Exception as e:
        print(f"Error selecting user: {e}")
        return None
    finally:
        db.close()

def select_or_create_user() -> Optional[models.User]:
    """Main function to handle user selection or creation."""
    while True:
        print("\n--- Account Management ---")
        print("1. Create new account")
        print("2. Select existing account")
        print("3. Exit")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            user = create_account()
            if user:
                return user
        elif choice == "2":
            user = select_user()
            if user:
                return user
        elif choice == "3":
            return None
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def create_game_file(user: models.User) -> Optional[models.GameFiles]:
    """Create a new game file for the user."""
    db = database.SessionLocal()
    try:
        print("\n--- Create New Game File ---")
        print("What game are you playing?")
        selected_game = game_choice()
        
        print(f"You are playing {selected_game} Version")
        print("What is your trainer name?")
        trainer_name = input().strip()
        
        if not trainer_name:
            print("Trainer name cannot be empty.")
            return None
        
        # Create new game file
        new_game_file = models.GameFiles(
            user_id=user.id,
            trainer_name=trainer_name,
            game_name=selected_game,
            gym_progress=[],
            route_progress=[]
        )
        db.add(new_game_file)
        db.commit()
        db.refresh(new_game_file)
        print(f"Game file created: {trainer_name} - {selected_game}")
        return new_game_file
    except Exception as e:
        db.rollback()
        print(f"Error creating game file: {e}")
        return None
    finally:
        db.close()

def select_game_file(user: models.User) -> Optional[models.GameFiles]:
    """Select an existing game file for the user."""
    db = database.SessionLocal()
    try:
        game_files = db.query(models.GameFiles).filter(
            models.GameFiles.user_id == user.id
        ).all()
        
        if not game_files:
            print("No game files found for this user.")
            return None
        
        print("\nSelect a game file:")
        for i, game_file in enumerate(game_files, 1):
            pokemon_count = len(game_file.owned_pokemon) if game_file.owned_pokemon else 0
            print(f"{i}. {game_file.trainer_name} - {game_file.game_name} ({pokemon_count} pokemon)")
        
        while True:
            try:
                choice = input("\nEnter the number of the game file (or '0' to go back): ").strip()
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(game_files):
                    selected_game_file = game_files[choice_num - 1]
                    db.refresh(selected_game_file)
                    return selected_game_file
                else:
                    print(f"Please enter a number between 1 and {len(game_files)}:")
            except ValueError:
                print("Please enter a valid number:")
    except Exception as e:
        print(f"Error selecting game file: {e}")
        return None
    finally:
        db.close()

def select_or_create_game_file(user: models.User) -> Optional[models.GameFiles]:
    """Main function to handle game file selection or creation."""
    while True:
        print("\n--- Game File Management ---")
        print("1. Create new game file")
        print("2. Select existing game file")
        print("3. Go back to user selection")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "1":
            game_file = create_game_file(user)
            if game_file:
                return game_file
        elif choice == "2":
            game_file = select_game_file(user)
            if game_file:
                return game_file
        elif choice == "3":
            return None
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

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

def starter(game: str, game_file_id: int):
    """Select and add starter pokemon to the game file."""
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
                    print("Invalid starter. Please choose from the list above:")
                
                # search for starter in all_pokemon db
                starter_data = db.query(models.AllPokemon).filter(models.AllPokemon.name == starter_selected).first()

                if starter_data:
                    added_pokemon = add_to_party(starter_data, game_file_id)
                    add_to_party_database(added_pokemon, game_file_id, db)

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
            exit()
        
         

def team():
    global current_game_file
    
    if not current_game_file:
        print("No game file selected. Please restart the application.")
        return
    
    db = database.SessionLocal()
    try:
        print("Team Status:")
        # Get party pokemon for the current game file
        party_pokemon_list = db.query(models.PartyPokemon).join(
            models.OwnedPokemon
        ).filter(
            models.OwnedPokemon.game_file_id == current_game_file.id
        ).all()


        if party_pokemon_list:
            for party_pokemon in party_pokemon_list:
                pokemon = party_pokemon.owned_pokemon
                if not pokemon:
                    continue
                print("Pokemon: " + pokemon.name)
                print("Nickname: " + (pokemon.nickname or "None"))
                print("Level: " + str(pokemon.level))
                print("Type(s): " + str(pokemon.types))
                print("-----------\n")

            print("Would you like to edit any information of a pokemon?: (y = yes)")
            edit = input().lower()
            if(edit == "y"):
                edit_pokemon(party_pokemon_list, db)
        else:
            print("Team is empty!")
    finally:
        db.close()



def edit_pokemon(party_pokemon_list, db):
    global current_game_file
    
    if not current_game_file:
        print("No game file selected.")
        return
    
    print("Which pokemon would you like to edit?: ")

    # Get party pokemon for the current game file
    party_pokemon = db.query(models.PartyPokemon).join(
        models.OwnedPokemon
    ).filter(
        models.OwnedPokemon.game_file_id == current_game_file.id
    ).all()
    i = 1
    for party_pokemon_entry in party_pokemon:
        pokemon = party_pokemon_entry.owned_pokemon
        if pokemon:
            print(str(i) + ": " + pokemon.name)
        i += 1 
    

    choice = int(input().lower())
    selected_party_pokemon = party_pokemon[choice - 1]
    poke_data = selected_party_pokemon.owned_pokemon
    if not poke_data:
        print("Error: Pokemon data not found.")
        return 
        
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
    # call global var
    global current_game_file
    
    if not current_game_file:
        print("No game file selected. Please restart the application.")
        return
    
    db = database.SessionLocal()
    try:
        # get current game file's 'route progression'
        game_file = db.query(models.GameFiles).filter(
            models.GameFiles.id == current_game_file.id
        ).first()
        
        if game_file:
            route_progress_value = getattr(game_file, 'route_progress', None)
            route_progress = list(route_progress_value) if route_progress_value is not None else []
        else:
            route_progress = []
        
    except Exception:
        print("Error fetching route progression data")
        return

    print("Routes discovered: " + str(route_progress))

    # get versions routes ordered 

    try:
        version_data = db.query(models.Version).filter(models.Version.version_name == current_game_file.game_name).first()
        if not version_data:
            raise Exception("Version name not found in database!")
        
        locations_ordered_value = getattr(version_data, 'locations_ordered', None)
        # Ensure it's a list, not a Column type
        if locations_ordered_value is None:
            locations_ordered = []
        else:
            locations_ordered = list(locations_ordered_value)

    except Exception:
        return
    
   
    locations_undiscovered = list_difference(locations_ordered, route_progress)

    
def view_locations(upcoming_locations: list):
    LOCATIONS_TO_SHOW = 3

    while True:
        print("Enter the co-responding location # to view & edit the location!: ")
        print("Upcoming Locations: (enter '0' to quit): ")
        if len(upcoming_locations) < 3:
            for i in range(len(upcoming_locations)):
                print(str(i+1) + ":" + upcoming_locations[i])

        else:
            for i in range(LOCATIONS_TO_SHOW):
                print(str(i+1) + ":" + upcoming_locations[i])
            upcoming_locations = upcoming_locations[:LOCATIONS_TO_SHOW]
        
        choice = int(input())
        if choice == 0: return
        elif choice - 1 > LOCATIONS_TO_SHOW or choice - 1> len(upcoming_locations):
            print("Please select one of the following numbers: ")
        else:
            location_to_view = upcoming_locations[choice - 1]
            
    



def list_difference(list1, list2):
    result = list1.copy()
    for item in list2:
        if item in result:
            result.remove(item)
    return result

                
   
def save_to_storage():
    """
    Save game progress to storage.json in the format specified above.
    Gets party pokemon from DB and formats all data according to the JSON structure.
    """
    global current_game_file
    
    if not current_game_file:
        print("No game file selected. Cannot save.")
        return
    
    db = database.SessionLocal()
    try:
        # Get party pokemon for the current game file
        party_pokemon_list = db.query(models.PartyPokemon).join(
            models.OwnedPokemon
        ).filter(
            models.OwnedPokemon.game_file_id == current_game_file.id
        ).all()
        
        # Convert party pokemon to dictionary format with all fields
        party_pokemon_json = []
        for party_pokemon in party_pokemon_list:
            pokemon = party_pokemon.owned_pokemon
            if not pokemon:
                continue
                
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
                "nature": pokemon.nature.value if pokemon.nature else None,
                "ability": pokemon.ability,
                "types": pokemon.types,
                "level": pokemon.level,
                "gender": pokemon.gender,
                "evolution_data": pokemon.evolution_data,
                "sprite": pokemon.sprite,
                "created_at": created_at_str
            }
            party_pokemon_json.append(pokemon_dict)
        
        # Format trainer_data from current game file
        trainer_name = current_game_file.trainer_name
        game_name = current_game_file.game_name
        
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


def add_to_party(pokemon_data, game_file_id: int):
    """Create an OwnedPokemon and return it. The PartyPokemon will be created separately."""
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
        nickname = input().strip()
    else:
        nickname = None

    print("It's nature?:")
    nature_input = input().strip()
    # Try to match the nature enum
    nature = None
    try:
        nature = models.Nature[nature_input.upper()]
    except (KeyError, AttributeError):
        # If not found, try to find case-insensitive match
        for n in models.Nature:
            if n.value.lower() == nature_input.lower():
                nature = n
                break

    print("It's ability?")
    print(abilities)
    while True:
        ability = input().strip()
        # Case-insensitive match
        matching_ability = None
        for ab in abilities:
            if ab.lower() == ability.lower():
                matching_ability = ab
                break
        if matching_ability:
            ability = matching_ability
            break
        print("Invalid ability. Please choose from the list above:")
    
    created_at = datetime.now()

    # Create OwnedPokemon first
    owned_pokemon = models.OwnedPokemon(
        game_file_id=game_file_id,
        poke_id=poke_id,
        name=name,
        nickname=nickname,
        nature=nature,
        ability=ability,
        types=types,
        level=5,
        gender=gender,
        status=models.Status.PARTY,
        evolution_data=evolution_data,
        sprite=sprite,
        created_at=created_at
    )

    return owned_pokemon



def add_to_party_database(owned_pokemon: models.OwnedPokemon, game_file_id: int, db: Session):
    """Add pokemon to database and create PartyPokemon entry."""
    try:
        # Add OwnedPokemon first
        db.add(owned_pokemon)
        db.flush()  # Flush to get the ID
        
        # Create PartyPokemon entry
        party_pokemon = models.PartyPokemon(
            game_file_id=game_file_id,
            owned_pokemon_id=owned_pokemon.id
        )
        db.add(party_pokemon)
        db.commit()
        print("added to party!")
    except Exception as e:
        db.rollback()
        print(f"Error adding pokemon to database: {e}")
        raise



if __name__ == "__main__":
    main()

