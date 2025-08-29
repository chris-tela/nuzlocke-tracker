'''
File is used to populate database with data from the PokeAPI.
'''

import requests
import os
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
            sprite = sprite,
            created_at = created_at
        )
        db.add(pokemon)
        db.commit()
        index += 1
    db.close()

    return {"message": "Pokemon populated successfully"}

# initalize all versions in the database
# currently sample code for unova region
@app.post("/populate/region/{region_id}")
def populate_region(region_id: int, db: Session = Depends(database.get_db)):
    response = requests.get(f"https://pokeapi.co/api/v2/region/{region_id}")
    region = response.json()
    region_name = region["name"]
    regional_cities = utils.get_region_locations(region_name)
    '''
    for version in region["version_groups"]:
        version_name = version["name"]
        version_url = version["url"]
        version_data = requests.get(version_url).json()
        version_id = int(version_data["id"])

        if version_name == "black-white":
            locations_ordered = utils.get_region_locations_ordered(utils.BW_LOCATIONS_ORDERED, region_name)
        elif version_name == "black-2-white-2":
            locations_ordered = utils.get_region_locations_ordered(utils.BW2_LOCATIONS_ORDERED, region_name)
        else:
            locations_ordered = []


        regional_cities = utils.get_region_locations(region_name);
        version = models.Version(
            region_name = region_name,
            region_id = region_id,
            version_name = version_name,
            version_id = version_id,
            regional_cities = regional_cities,
            locations_ordered = locations_ordered
        )
        '''
    regoin = models.Region(
        region_id = region_id,
        region_name = region_name,
        regional_cities = regional_cities
    )
    db.add(region)
    db.commit()
    db.close()

    return {"message": "Region populated successfully"}

@app.post("/populate/version/{version_id}")
def populate_version(version_id: int, db: Session = Depends(database.get_db)):
    version = requests.get(f"https://pokeapi.co/api/v2/version/{version_id}").json()
    version_name = version["name"]
    version_id = version["id"]
    ## placeholder for now
    if version_name == "black" or version_name == "white":
        locations_ordered = utils.get_region_locations_ordered(utils.BW_LOCATIONS_ORDERED, version_name)
    elif version_name == "black-2" or version_name == "white-2":
        locations_ordered = utils.get_region_locations_ordered(utils.BW2_LOCATIONS_ORDERED, version_name)
    else:
        locations_ordered = []
    version = models.Version(
        version_id = version_id,
        version_name = version_name,
        locations_ordered = locations_ordered
    )
    db.add(version)
    db.commit()
    db.close()
    return {"message": "Version populated successfully"}

@app.get("/versions")
def get_versions(db: Session = Depends(database.get_db)):
    """Get all versions in the database"""
    versions = db.query(models.Version).all()
    return {
        "versions": [
            {
                "version_id": v.version_id,
                "version_name": v.version_name,
                "region_name": v.region_name,
                "region_id": v.region_id
            }
            for v in versions
        ]
    }

@app.post("/populate/routes/{version_id}")
def populate_route_encounters(version_id: int, db: Session = Depends(database.get_db)):
    # First check if the version exists
    version = db.query(models.Version).filter(models.Version.version_id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail=f"Version with ID {version_id} not found in database. Please populate the region first.")
    
    for loc in version.locations_ordered:
        try:
            loc_lower = loc.lower()
            data = utils.get_encounters(loc_lower + "-area")
        except Exception as e:
            print(f"Error at {loc}: {e}")
            continue
        try:
            route_encounter = models.Route_Encounters(
                name = loc_lower,
                data = data
            )
            db.add(route_encounter)
        except Exception as e:
            print(f"Error at {loc}: {e}")
            raise HTTPException(status_code=500, detail=f"Error at {loc}: {e}")
    db.commit()
    db.close()
    return {"message": "Route encounters populated successfully"}



        








