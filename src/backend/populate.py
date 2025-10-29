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
import utils

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
                pokemon_species = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{index}").json()
                chain_id = pokemon_species["evolution_chain"]["url"].split("/")[-2]
                chain = requests.get(f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/").json()
                evolution_data = evolution_parse(chain, name)
                

            except Exception as e:
                print(f"Error at {index}: {e}")
        else:
            break

        # insert into database
        
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
            sprite = sprite,
            created_at = created_at
        )
        db.add(pokemon)
        db.commit()
        index += 1
    db.close()

    return {"message": "Pokemon populated successfully"}

def evolution_parse(chain: str, name: str):
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
                            "evolution_details": [{"min_level": evo["evolution_details"][0]["min_level"]}, {"trigger": {"name": evo["evolution_details"][0]["trigger"]["name"]}}]
                        }
                    })
        # stage 2 --> stage 3
            if(str(chain["chain"]["evolves_to"][0]["species"]["name"]) == str(data["name"])):
                for evo in chain["chain"]["evolves_to"][0]["evolves_to"]:
                    data["evolution_data"].append({
                        "evolves_to": {
                            "species": evo["species"]["name"],
                            "evolution_details": [{"min_level": evo["evolution_details"][0]["min_level"]}, {"trigger": {"name": evo["evolution_details"][0]["trigger"]["name"]}}]
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
            print(vers_id)
            exists = db.query(models.Version).filter(models.Version.version_id == vers_id).first()
            if exists:
                continue

            version_names.append(version["name"])
            version_ids.append(vers_id)
        try:
            string = version_group_name.replace("-","_").upper() + "_locations_ordered".upper()
            locations_ordered = utils.get_region_locations_ordered(string, gen.region_name)
        except Exception as e:

            continue

        
        for i in range(len(version_names)):
            version = models.Version(
                generation_id = gen.generation_id,
                version_id = version_ids[i],
                version_name = version_names[i],
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
        try:
            loc_lower = loc.lower()
            data = utils.get_encounters(loc_lower, generation.region_name, version.version_name)
        except Exception as e:
            continue
        try:
            route_encounter = models.Route(
                name = loc_lower,
                version_id = version.version_id,
                region_id = generation.region_id,
                data = data
            )
            db.add(route_encounter)
        except Exception as e:
            print(f"Error at {loc}: {e}")
            raise HTTPException(status_code=500, detail=f"Error at {loc}: {e}")
    db.commit()
    db.close()
    return {"message": "Route encounters populated successfully"}



        








