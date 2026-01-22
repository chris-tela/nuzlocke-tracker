import requests
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException
from db import database, models


ALLOWED_CONDITIONS = ["time-morning", "time-day", "time-night", "season-spring", "season-summer", "season-autumn", "season-winter", "story-progress", "swarm-no", "radio-off", "item-none"]


# goal:
# write a function that takes a route and returns a list of pokemon that can be encountered

def get_encounters(route: str, region_name: str, version_name: str, derived_from: str = "", db: Optional[Session] = None):
    # check if location area exists, if not, check if location exists, otherwise return function

    
    if (route.startswith(region_name + "-route") or route.startswith(region_name + "-sea-route")) and not route.__contains__("area"):
        route_with_area = route + "-area"
        
    # try with '-area', try without (inconsenstiences in API on route naming)
    try:
        route_area = requests.get(f"https://pokeapi.co/api/v2/location-area/{route_with_area.lower()}").json()
    
    except Exception:
        try:
            route_area = requests.get(f"https://pokeapi.co/api/v2/location-area/{route.lower()}").json()
        except Exception:
            try:
                get_location(route, region_name, version_name)
            except Exception:
                print("get location exception")

 
            
    try:
        encounters = route_area["pokemon_encounters"]
    except:
        raise Exception("Location contains no encounters")


    encounter_data = []
    for encounter in encounters:
        for version in encounter["version_details"]:
            if version["version"]["name"] == version_name:
                name = encounter["pokemon"]["name"]
                min_level = 100
                max_level = 1
                encounter_details = []
                skip_pokemon = False
                
                    
                for details in version["encounter_details"]:
                    try: 
                        condition = details["condition_values"][0]["name"]
                    except Exception:
                        condition = None
                    # if conditon is a condition listed but not supported, skip full pokemon instance
                    if not(condition in ALLOWED_CONDITIONS or condition is None or condition.startswith("story-progress")):
                        skip_pokemon = True
                        break

                    min_level = min(min_level, details["min_level"])
                    max_level = max(max_level, details["max_level"])

                    chance = int(details["chance"])
                    method = details["method"]["name"]

                    # if detail already has the same method & condition --> is chance higher? --> YES: keep higher chance, NO: skip
                    add_to_details = True
                    for enc in encounter_details:
                        if enc["method"] == method and enc["condition"] == condition:
                            enc["chance"] += chance
                            add_to_details = False
                    if add_to_details:
                        encounter_details.append({"method": method, "condition": condition, "chance": chance})

                        

                    
                if not skip_pokemon:
                    encounter_data.append([{"name": name}, {"min_level": min_level}, {"max_level": max_level}, {"game_name": version_name}, {"region_name": region_name}, encounter_details])
    if encounter_data == []:
        raise Exception("Location contains no encounters")


    # Add route if we successfully got data
    # Create a session if one wasn't provided
    session_provided = db is not None
    if db is None:
        db = database.SessionLocal()
    version = db.query(models.Version).filter(models.Version.version_name == version_name).first()
    if version is not None:
        version_id = version.version_id
        region_id = version.generation_id
    

    if route.__contains__("sea-route"):
        route = route.replace("sea-", "")
    try:
        print(f"Adding route: {route}")
        route_encounter = models.Route(
            name = route,
            version_id = version_id,
            region_id = region_id,
            derives_from = derived_from,
            data = encounter_data
        )
        db.add(route_encounter)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error at {route}: {e}")
        raise HTTPException(status_code=500, detail=f"Error at {route}: {e}")
    finally:
        # Only close if we created the session ourselves
        if not session_provided:
            db.close()

'''
function is used when a location has multiple areas, all containing encounters that need to be condensed into a single area that isn't in the location-area api
used as a 'helper' for get_encounters
'''
def get_location(loc: str, region: str,  version: str):
    location = requests.get(f"https://pokeapi.co/api/v2/location/{loc.lower()}").json()
    try:
        areas = location["areas"]
    except Exception as e:
        raise Exception("Location contains no areas: " + str(e))
    
    if len(areas) <= 1:
        raise Exception("Location contains one or none areas, and does not need to be condensed")
    

    areas_encounters = []
    for area in areas:
        try:
            area_encounter = get_encounters(area["name"], region, version, loc)
            areas_encounters.append(area_encounter)
        except Exception as e:
            continue


    if len(areas_encounters) == 0:
        raise Exception()
    # condense areas_encounters into a single list
    # iterate through each pokemon, find its min and max level across all areas and add to condensed_encounters

   
    # condensed_encounters = []
    # pokemon_list = []
    # for x in range(len(areas_encounters)):
    #     for y in range(len(areas_encounters[x])):
    #         print("test4")
    #         # Extract values from dictionary structure: [{"name": name}, {"min_level": min_level}, {"max_level": max_level}, {"game_name": version_name}, {"region_name": region_name}, encounter_details]
    #         pokemon = areas_encounters[x][y][0]["name"]
    #         min_level = areas_encounters[x][y][1]["min_level"]
    #         max_level = areas_encounters[x][y][2]["max_level"]
    #         encounter_details = areas_encounters[x][y][5]  # This is already a list of dictionaries
            
    #         if pokemon not in pokemon_list:
    #             pokemon_list.append(pokemon)
    #             condensed_encounters.append([{"name": pokemon}, {"min_level": min_level}, {"max_level": max_level}, {"game_name": version}, {"region_name": region}, encounter_details])

    #         else:
    #             # get data for pokemon from condensed_encounters
    #             for z in range(len(condensed_encounters)):
    #                 if condensed_encounters[z][0] == pokemon:
    #                     existing_min_level = condensed_encounters[z][1]
    #                     existing_max_level = condensed_encounters[z][2]
    #                     # Update min/max levels - take the minimum min_level and maximum max_level
    #                     updated_min_level = min(existing_min_level, min_level)
    #                     updated_max_level = max(existing_max_level, max_level)
    #                     print("tset2")
    #                     existing_encounter_details = condensed_encounters[z][5]
                        
    #                     merged_values = merge_encounters(existing_encounter_details, encounter_details)
                        
    #                     # Remove old entry and add updated one
    #                     condensed_encounters.pop(z)
    #                     condensed_encounters.append([{"name":pokemon}, {"min_level": updated_min_level}, {"max_level": updated_max_level}, {"game_name": version}, {"region_name": region}, merged_values])
    #                     break

    # return condensed_encounters

def merge_encounters(list1, list2):
    merged = {}

    for enc in list1 + list2:
        key = (enc["method"], enc["condition"])

        if key not in merged:
            merged[key] = enc.copy()
        else:
            # keep highest chance between duplicate method conditions
            merged[key]["chance"] = max(
                merged[key]["chance"],
                enc["chance"]
            )

    return list(merged.values())




if __name__ == "__main__":
    # Create a database session for script execution
    db_session = database.SessionLocal()
    try:
        get_encounters("johto-sea-route-41", "johto", "heartgold", "", db_session)
    finally:
        db_session.close()
