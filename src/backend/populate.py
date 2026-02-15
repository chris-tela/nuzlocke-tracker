'''
File is used to populate database with data from the PokeAPI.
'''

import requests
import os
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, HTTPException
from db import models, database
import utils, route

head = os.getenv("HEAD")
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# initalize all pokemon in the database
@app.post("/populate/pokemon")
async def populate_pokemon(db: Session = Depends(database.get_db)):
    index = 1
    while True:
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{index}")

        if response.status_code == 200:
            try:
                pokemon = response.json()
                id, poke_id = pokemon["id"], pokemon["id"]
                name = pokemon["forms"][0]["name"]
                types = [pokemon["types"][i]["type"]["name"] for i in range(len(pokemon["types"]))]
                past_types = get_past_types(pokemon)
                abilities = [pokemon["abilities"][i]["ability"]["name"] for i in range(len(pokemon["abilities"]))]
                weight = pokemon["weight"]
                stats = pokemon["stats"]
                base_hp = stats[0]["base_stat"]
                base_attack = stats[1]["base_stat"]
                base_defense = stats[2]["base_stat"]
                base_special_attack = stats[3]["base_stat"]
                base_special_defense = stats[4]["base_stat"]
                base_speed = stats[5]["base_stat"]
                sprite = pokemon["sprites"]["front_default"]
                created_at = datetime.now()

                # evolution logic
                evolution_data = []  # Initialize empty array
                try:
                    pokemon_species = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{index}").json()
                    chain_id = pokemon_species["evolution_chain"]["url"].split("/")[-2]
                    chain = requests.get(f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/").json()
                    evolution_result = evolution_parse(chain, name)
                    evolution_data = evolution_result.get("evolution_data", [])  # Extract just the array
                except Exception as evo_error:
                    print(f"Evolution error at {index}: {evo_error}")

            except Exception as e:
                print(f"Error at {index}: {e}")
                continue  # Skip to next iteration if main pokemon data fails
        else:
            break

        # insert into database
        # Convert sprite to webp if sprite URL exists
        if sprite:
            try:
                utils.convert_image_to_webp(sprite, name)
            except Exception as img_error:
                print(f"Image conversion error for {name} (ID: {index}): {img_error}")
                # Continue even if image conversion fails
        else:
            print(f"Warning: No sprite found for {name} (ID: {index})")

        pokemon = models.AllPokemon(
            id = id,
            poke_id = poke_id,
            name = name,
            types = types,
            abilities = abilities,
            weight = weight,
            base_hp = base_hp,
            base_attack = base_attack,
            base_defense = base_defense,
            base_special_attack = base_special_attack,
            base_special_defense = base_special_defense,
            base_speed = base_speed,
            evolution_data = evolution_data,
            created_at = created_at
        )
        db.add(pokemon)
        db.commit()
        index += 1
    db.close()

    return {"message": "Pokemon populated successfully"}

'''
{
    "generation": 5,
    "past_types": ["normal"]
}

'''

def get_past_types(pokemon: dict):
    types = []
    generation = None
    try:
        for data in pokemon.get("past_types", []):
            generation = data["generation"]["url"].split("/")[-2]
            for type_slot in data["types"]:
                types.append(type_slot["type"]["name"])
    except Exception as e:
        return {}
    result = {"generation": generation, "past_types": types}
    return result


response = requests.get(f"https://pokeapi.co/api/v2/pokemon/jigglypuff")
get_past_types(response.json())

def evolution_parse(chain: dict, name: str):
 # format of 'chain' in pokemon_attributes:
    # "evolution_data": 
    # [
    #     {
    #         "evolves_to": {
    #             "species": "vaporeon", 
    #             "evolution_details": [{"min_level": 16}, {"trigger": {"name": "level-up"}}]
    #         }
    #     }
    # ]
    data = {"name": name, "evolution_data": []}

    try:
        if(len(chain["chain"]["evolves_to"]) > 0):
            # stage 1 --> stage 2
            if(str(chain["chain"]["species"]["name"]) == str(data["name"])):
                for evo in chain["chain"]["evolves_to"]:
                    data["evolution_data"].append({
                        "evolves_to": {
                            "species": evo["species"]["name"],
                            "evolution_details": [{"min_level": evo["evolution_details"][0]["min_level"], "trigger": {"name": evo["evolution_details"][0]["trigger"]["name"]}}]
                        }
                    })
        # stage 2 --> stage 3
            if(str(chain["chain"]["evolves_to"][0]["species"]["name"]) == str(data["name"])):
                for evo in chain["chain"]["evolves_to"][0]["evolves_to"]:
                    data["evolution_data"].append({
                        "evolves_to": {
                            "species": evo["species"]["name"],
                            "evolution_details": [{"min_level": evo["evolution_details"][0]["min_level"], "trigger": {"name": evo["evolution_details"][0]["trigger"]["name"]}}]
                        }
                    })
    except Exception as e:
        print(e)

    # pretty print json data
    json_formatted_str = json.dumps(data, indent=2)
    print(json_formatted_str)

    return data


# initalize all versions in the database
@app.post("/populate/generation/{generation_id}")
def populate_generation(generation_id: int, db: Session = Depends(database.get_db)):
    response = requests.get(f"https://pokeapi.co/api/v2/generation/{generation_id}")
    generation = response.json()
    pokemon_list = []
    for pokemon in generation["pokemon_species"]:
        pokemon_list.append(pokemon["name"])

    version_groups = []
    for version in generation["version_groups"]:
        version_name = version["name"]
        if(not version_name.endswith("japan")):
            version_groups.append(version_name)

    region_details = generation["main_region"]
    region_name = region_details["name"]
    region_url = region_details["url"]
    print(region_url)
    region_response = requests.get(region_url).json()
    print(region_response)
    region_id = region_response["id"]
    regional_cities =[]

    for loc in region_response["locations"]:
        regional_cities.append(loc["name"])

    generation = models.Generation(
        generation_id = generation_id,
        pokemon = pokemon_list,
        region_id = region_id,
        region_name = region_name,
        regional_cities = regional_cities,
        version_groups = version_groups
        )
    

    db.add(generation)
    db.commit()
    db.close()

    return {"message": "Generation populated successfully"}

@app.post("/populate/versions/{generation_id}")
def populate_versions(generation_id: int, db: Session = Depends(database.get_db)):

    gen = db.query(models.Generation).filter(models.Generation.generation_id == generation_id).first()
    if not gen:
        raise HTTPException(status_code=404, detail=f"Generation {generation_id} not found in database.")

    version_groups = gen.version_groups
    # proportinate to generation; all versions unique to a generation
    for version_group in version_groups:
        url = requests.get((f"https://pokeapi.co/api/v2/version-group/{version_group}")).json()
 
        version_group_name = url["name"]

        version_names = []
        version_ids = []
        for version in url["versions"]:
            vers_id = version["url"].split("/")[-2]
            
            exists = db.query(models.Version).filter(models.Version.version_id == vers_id).first()
            if exists:
                continue

            version_names.append(version["name"])
            version_ids.append(vers_id)
       
        try:
            string = version_group_name.replace("-","_").upper() + "_locations_ordered".upper()
            # hardcode unique cases
            if version_group_name == "heartgold-soulsilver":
                region_name = "johto"
                locations_ordered = utils.get_region_locations_ordered(string, region_name)
            elif version_group_name == "firered-leafgreen":
                region_name = "kanto"
                locations_ordered = utils.get_region_locations_ordered(string, region_name)
            else:
                locations_ordered = utils.get_region_locations_ordered(string, str(gen.region_name))
                region_name = gen.region_name
        except Exception as e:

            continue

        
        for i in range(len(version_names)):
            version = models.Version(
                generation_id = gen.generation_id,
                version_id = version_ids[i],
                version_name = version_names[i],
                region_name = region_name,
                locations_ordered = locations_ordered
            )
            db.add(version)
    db.commit()
    db.close()
    return {"message": "Versions populated successfully"}



@app.post("/populate/routes/{version_id}")
def populate_route(version_id: int, db: Session = Depends(database.get_db)):
    # First check if the version exists
    version = db.query(models.Version).filter(models.Version.version_id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail=f"Version with ID {version_id} not found in database. Please populate the region first.")
    #check if generation exists
    generation = db.query(models.Generation).filter(models.Generation.generation_id == version.generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail=f"Generation with ID {version.generation_id} not found in database. Please populate the region first.")
    
    for loc in version.locations_ordered:
        loc_lower = loc.lower()
        data = None
        route_name = None
        
        # Check if route already exists (either as original or sea route)
        sea_route = loc_lower[:len(str(version.region_name))] + "-sea" + loc_lower[len(str(version.region_name)):] if loc_lower.__contains__("route") else None
        existing_route = db.query(models.Route).filter(
            models.Route.version_id == version.version_id
        ).filter(
            (models.Route.name == loc_lower) | (models.Route.name == sea_route) if sea_route else (models.Route.name == loc_lower)
        ).first()
        
        if existing_route:
            print(f"Route {loc_lower} (or {sea_route}) already exists for version_id {version_id}, skipping...")
            continue
        
        # Try original location first
        try:
            data = route.get_encounters(loc_lower, str(version.region_name), str(version.version_name))
            route_name = loc_lower
        except Exception as e:
            # If it's a route and original fails, try sea route
            if sea_route:
                try:
                    print(f"Trying sea route: {sea_route}")
                    data = route.get_encounters(sea_route, str(version.region_name), str(version.version_name))
                    route_name = loc_lower
                except Exception:
                    continue
            else:
                continue
        
        # Add route if we successfully got data
        # if data and route_name:
        #     try:
        #         print(f"Adding route: {route_name}")
        #         route_encounter = models.Route(
        #             name = route_name,
        #             version_id = version.version_id,
        #             region_id = generation.region_id,
        #             data = data
        #         )
        #         db.add(route_encounter)
        #     except Exception as e:
        #         print(f"Error at {loc}: {e}")
        #         raise HTTPException(status_code=500, detail=f"Error at {loc}: {e}")
    db.commit()
    db.close() 
    return {"message": "Route encounters populated successfully"}

# @app.get("/populate/version/{version_name}/routes/{route_name}")
# def route(version_name: str, route_name: str, db: Session = Depends(database.get_db)):
         
#         try:
#             data = utils.get_encounters(route_name, "kanto", version_name)
#         except Exception:
#             sea_route = route_name[:len(str("kanto"))] + "-sea" + route_name[len(str("kanto")):]
#             print(sea_route)
#             data = utils.get_encounters(sea_route, "kanto", version_name)



#         print(data)

#         return data



def get_trainer_data_filename_from_game_name(game_name: str) -> str:
    """
    Map game_name to the corresponding trainer_data JSON filename.
    Uses naming convention from scrape/trainer_data directory.
    """
    game_name_lower = game_name.lower()
    
    # Map game names to trainer_data filenames based on actual file names
    trainer_data_map = {
        'red': 'red-blue_trainers.json',
        'blue': 'red-blue_trainers.json',
        'yellow': 'yellow_trainers.json',
        'gold': 'gold-silver_trainers.json',
        'silver': 'gold-silver_trainers.json',
        'crystal': 'crystal_trainers.json',
        'ruby': 'ruby-sapphire_trainers.json',
        'sapphire': 'ruby-sapphire_trainers.json',
        'emerald': 'ruby-sapphire_trainers.json',
        'firered': 'firered-leafgreen_trainers.json',
        'leafgreen': 'firered-leafgreen_trainers.json',
        'diamond': 'diamond-pearl_trainers.json',
        'pearl': 'diamond-pearl_trainers.json',
        'platinum': 'platinum_trainers.json',
        'heartgold': 'heartgold-soulsilver_trainers.json',
        'soulsilver': 'heartgold-soulsilver_trainers.json',
        'black': 'black-white_trainers.json',
        'white': 'black-white_trainers.json',
        'black-2': 'black-white-2_trainers.json',
        'white-2': 'black-white-2_trainers.json',
        # Handle PokeAPI naming variations
        'heart-gold': 'heartgold-soulsilver_trainers.json',
        'soul-silver': 'heartgold-soulsilver_trainers.json',
        'fire-red': 'firered-leafgreen_trainers.json',
        'leaf-green': 'firered-leafgreen_trainers.json',
    }
    
    return trainer_data_map.get(game_name_lower, f'{game_name_lower}_trainers.json')


@app.post("/populate/gyms")
def populate_gyms(db: Session = Depends(database.get_db)):
    """Populate gym table from trainer_data JSON files."""
    import os
    
    # Get all versions from database
    versions = db.query(models.Version).all()
    
    if not versions:
        raise HTTPException(status_code=404, detail="No versions found in database. Please populate versions first.")
    
    trainer_data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend",
        "scrape",
        "trainer_data"
    )
    
    # Map to track which files we've processed
    processed_files = {}
    
    for version in versions:
        # Get trainer data filename for this version using naming convention
        game_name = str(version.version_name)
        filename = get_trainer_data_filename_from_game_name(game_name)
        
        # Skip if we've already processed this file for another version
        if filename in processed_files:
            # Use the same gym data but create entries for this version
            gym_data = processed_files[filename]
            for gym_entry in gym_data:
                # Check if gym already exists for this game_name
                existing = db.query(models.Gym).filter(
                    models.Gym.game_name == game_name,
                    models.Gym.gym_number == gym_entry['gym_number']
                ).first()
                
                if not existing:
                    gym = models.Gym(
                        game_name=game_name,
                        gym_number=gym_entry['gym_number'],
                        gym_path=f"data/badges/{game_name}_{gym_entry['gym_number']}.webp",
                        location=gym_entry['location'],
                        trainer_name=gym_entry['trainer_name'],
                        trainer_image=gym_entry['trainer_image'],
                        badge_name=gym_entry['badge_name'],
                        badge_type=gym_entry['badge_type'],
                        pokemon=gym_entry['pokemon']
                    )
                    db.add(gym)
            continue
        
        # Load trainer data file
        file_path = os.path.join(trainer_data_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"Warning: Trainer data file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Trainer data not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_trainers = json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
        
        # Filter for gyms only (exclude Elite Four and Champion)
        gym_trainers = [
            trainer for trainer in all_trainers 
            if trainer.get('location') not in ['Elite Four', 'Champion'] 
            and trainer.get('gym_number') 
            and trainer.get('gym_number') != ''
        ]
        
        # Group by gym_number and create gym entries
        gyms_by_number = {}
        for trainer in gym_trainers:
            gym_num = int(trainer.get('gym_number'))
            
            if gym_num not in gyms_by_number:
                # First trainer for this gym - use their data
                gyms_by_number[gym_num] = {
                    'gym_number': gym_num,
                    'location': trainer.get('location', ''),
                    'trainer_name': trainer.get('trainer_name', ''),
                    'trainer_image': trainer.get('trainer_image', ''),
                    'badge_name': trainer.get('badge_name', ''),
                    'badge_type': trainer.get('badge_type', ''),
                    'pokemon': trainer.get('pokemon', [])
                }
            else:
                # Additional trainer for this gym - combine pokemon
                existing_pokemon = gyms_by_number[gym_num]['pokemon']
                new_pokemon = trainer.get('pokemon', [])
                # Add pokemon that aren't already in the list
                for poke in new_pokemon:
                    if poke not in existing_pokemon:
                        existing_pokemon.append(poke)
        
        # Store processed file data
        processed_files[filename] = list(gyms_by_number.values())
        
        # Create Gym entries for this version
        for gym_entry in gyms_by_number.values():
            # Check if gym already exists
            existing = db.query(models.Gym).filter(
                models.Gym.game_name == game_name,
                models.Gym.gym_number == gym_entry['gym_number']
            ).first()
            
            if existing:
                continue  # Skip if already exists
            
            gym = models.Gym(
                game_name=game_name,
                gym_number=gym_entry['gym_number'],
                gym_path=f"data/badges/{game_name}_{gym_entry['gym_number']}.webp",
                location=gym_entry['location'],
                trainer_name=gym_entry['trainer_name'],
                trainer_image=gym_entry['trainer_image'],
                badge_name=gym_entry['badge_name'],
                badge_type=gym_entry['badge_type'],
                pokemon=gym_entry['pokemon']
            )
            db.add(gym)
    
    db.commit()
    db.close()
    return {"message": "Gyms populated successfully"}


@app.post("/populate/types")
def populate_types(db: Session = Depends(database.get_db)):
    url = requests.get((f"https://pokeapi.co/api/v2/type/")).json()

    if url is None:
        raise HTTPException(status_code=404, detail=f"Types url not found in PokeAPI!")
    
    try:
        x = 1
        for pokemon_type in url["results"]:
            name = pokemon_type["name"]
            type_url = pokemon_type["url"]

            populated = populate_type(type_url)
            print(populated)
            pokemon_type = models.Type(
                id = x,
                type_name = populated[0],
                generation_introduction = populated[1],
                current_damage_relations=populated[2],
                past_damage_relations = populated[3]
            )
            db.add(pokemon_type)
            x +=1
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing types: {e}")
    db.commit()
    db.close()

    return {"message": "Types populated successfully!"}

def populate_type(url):
    url = requests.get(url).json()

    type_name = url["name"]
    generation_introduction = url["generation"]["url"].split("/")[-2]

    damage_relations = get_damage_relations(url["damage_relations"])
    try:
        all_past_damage_relations = []

        past_damage_relations_list = url["past_damage_relations"]

        if past_damage_relations_list:  # make sure list is not empty
            
            

            for past_relation in past_damage_relations_list:
                past_damage = get_damage_relations(past_relation["damage_relations"])
                past_damage["on_and_backwards"] = past_relation["generation"]["url"].split("/")[-2]  # fixed assignment
                all_past_damage_relations.append(past_damage)
        else:
            all_past_damage_relations = []

    except (KeyError, IndexError, TypeError):
        all_past_damage_relations = []

    
    return (type_name, generation_introduction, damage_relations, all_past_damage_relations)
    

# {"double_damage_from": [x,x,x], ...}
def get_damage_relations(relations_dict: dict):
    # relations_dict is a dict like damage_relations

    try:
        for key, relation_list in relations_dict.items():  # loop over "double_damage_from", etc.
            for relation in relation_list:
                relation.pop("url", None)
    except Exception:
        pass
    return relations_dict


@app.post("/populate/moves")
def populate_moves(db: Session = Depends(database.get_db)):
    listing = requests.get("https://pokeapi.co/api/v2/move?limit=1000").json()
    if listing is None:
        raise HTTPException(status_code=404, detail="Moves listing not found!")

    try:
        for move_entry in listing["results"]:
            move_data = requests.get(move_entry["url"]).json()
            move_id = move_data["id"]

            # Idempotency — skip if already exists
            existing = db.query(models.Move).filter(models.Move.id == move_id).first()
            if existing:
                continue

            # Extract English short_effect
            effect = None
            for entry in move_data.get("effect_entries", []):
                if entry["language"]["name"] == "en":
                    effect = entry["short_effect"]
                    break

            move = models.Move(
                id=move_id,
                name=move_data["name"],
                type_name=move_data["type"]["name"],
                power=move_data["power"],
                pp=move_data["pp"],
                accuracy=move_data["accuracy"],
                damage_class=move_data["damage_class"]["name"],
                effect=effect,
                generation=int(move_data["generation"]["url"].split("/")[-2]),
                priority=move_data["priority"],
            )
            db.add(move)

            if move_id % 50 == 0:
                db.commit()
                print(f"Committed moves up to ID {move_id}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing moves: {e}")

    db.commit()
    db.close()
    return {"message": "Moves populated successfully!"}






