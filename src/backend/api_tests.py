# test api and wrapper

#wrapper api
import pokebase as pb
import re
import requests
import time
import json

# black and white locations ordered
BW_LOCATIONS_ORDERED = ["Nuvema Town", "Juniper's Lab", "Route 1", "Accumula Town", "Route 2", "Striaton City", "The Dreamyard", "Striaton Gym",
                           "Route 3", "Wellspring Cave", "Nacrene City", "Nacrene Gym", "Pinwheel Forest", "Skyarrow Bridge", "Castelia City", "Castelia Gym",
                           "Route 4", "Desert Resort", "Relic Castle", "Nimbasa City", "Nimbasa Gym", "Anville Town", "Route 5", "Driftveil Drawbridge", "Driftveil City", "Cold Storage", "Driftveil Gym",
                           "Route 6", "Chargestone Cave", "Mistralton City", "Route 7", "Celestial Tower", "Mistralton Gym", "Route 17", "Route 18", "P2 Laboratory", "Mistralton Cave", "Rumination Field",
                           "Twist Mountain", "Icirrus City", "Icirrus Gym", "Dragonspiral Tower", "Relic Castle", "Nacrene Museum", "Route 8", "Moor of Icirrus", "Tubeline Bridge", "Route 9",
                           "Opelucid City", "Opelucid Gym", "Route 10", "Victory Road", "Opelucid City", "Opelucid Gym", "Route 10", "Victory Road",
                           "Nuvema Town", "The Dreamyard", "The Royal Unova", "Relic Castle", "Nimbasa City", "Driftveil City", "Chargestone Cave", "Twist Mountain", "Challenger's Cave", "Opelucid City",
                           "Route 11", "Village Bridge", "Route 12", "Lacunosa Town", "Route 13", "Giant Chasm", "Undella Town", "Undella Bay", "Abyssal Ruins", "Route 14", "Abundant Shrine",
                           "Black City", "White Forest", "Route 15", "Poké Transfer Lab", "Marvelous Bridge", "Route 16", "Lostlorn Forest"
                           ]


# goal:
# write a function that takes a route and returns a list of pokemon that can be encountered
# 1. include its min level & max level
# 2. include the encounter method (dark grass, etc)
# 3. have a list for each version of the game (black, white, black2, etc)
# output: [[pokemon, min_level, max_level, version], [pokemon, min_level, max_level, version], ...]

# [[liepard, 19, 21, black], [liepard, 19, 23, white-2]]
# location_area --> pokemon_encounters[list] --> pokemon --> name
#                                            --> version_details[list] --> version
#                                                                      --> encounter_details[list] --> min_level (iterated), max_level (iterated), method

def get_encounters(route: str) -> list[list]:
    route_area = requests.get(f"https://pokeapi.co/api/v2/location-area/{route.lower()}").json()
    try:
        encounters = route_area.pokemon_encounters
    except:
        return []
    encounter_data = []
    for encounter in encounters:
        name = encounter.pokemon.name
        version_details = encounter.version_details

        for vers_details in version_details:
            version = vers_details.version
            iter = 0

            #encounter_details = version_details[0].encounter_details
            min_level, max_level = 100, 0
            for details in vers_details.encounter_details:
                    if(min_level > details.min_level):
                        min_level = details.min_level
                    if(max_level < details.max_level):
                        max_level = details.max_level
            iter += 1

            encounter_data.append([name, min_level, max_level, version])

    return encounter_data


# goal: create a method that parses all cities inside a region. 
# ex, take it a region like unova, spit out all cities, routes, caves, etc, in the game.

def get_region_locations(region: str) -> list[str]:
    reg = requests.get(f"https://pokeapi.co/api/v2/region/{region.lower()}").json()
    locations = []
    for loc in reg.locations:
         str_loc = str(loc)
         if(str_loc.startswith("<location-") and str_loc.endswith(">")):
              str_loc = str_loc[len("<location-"):-1]
         locations.append(str_loc)
    return locations

# goal: organize the locations by start of the game to finished in a walkthrough format
# parse cities to be readable by wrapper, and remove cities/locations that do not have any encounters

def get_region_locations_ordered(location_list: list[str], region: str) -> list[str]:
    # Create translation table for character replacements
    translation_table = str.maketrans({
        ' ': '-',
        "'": '',
        '.': '',
        ',': ''
    })
    
    cleaned_locations = []
    for loc in location_list:
        loc_lower = loc.lower()
        
      #  if pb.location_area(loc_lower) is None:
        #    continue
        if cleaned_locations.__contains__(loc_lower):
            continue
        
        # Handle route prefix
        if loc_lower.startswith("route"):
            loc_lower = loc_lower.replace("route", region.lower() + "-route")
        else:
            if pb.location_area(loc_lower) is None:
                continue
        # Apply all replacements at once using translate
        cleaned_loc = loc_lower.translate(translation_table)
        cleaned_locations.append(cleaned_loc)
        print(cleaned_loc)

    return cleaned_locations


# goal: given a pokemon, return a dictionary of its attributes
# base stats removed for now bc of complications between generations
# ex: {"name": "liepard", 'nickname": "cat", id": 510, "nature": "timid", "abilities": ["intimidate", "quick feet", "prankster"], "types": ["dark", "normal"], "sprite": "sprite.png", "level_caught": 19, "weight": 37, "gender": "male"}
# evolution: "none"
def get_pokemon_encounters(poke: str) -> dict:
    pokemon = requests.get(f"https://pokeapi.co/api/v2/pokemon/{poke.lower()}").json()
    pokemon_species = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{poke.lower()}").json()
    
    pokemon_attributes = {}

    # replace hard-coded attributes with user-inputted attributes
    # TODO: user-inputted attributes (when a pokemon is caught)
    pokemon_attributes["name"] = pokemon["name"]
    pokemon_attributes["nickname"] = "my pokemon"
    pokemon_attributes["id"] = pokemon["id"]
    pokemon_attributes["nature"] = "timid"
    pokemon_attributes["abilities"] = [pokemon["abilities"][i]["ability"]["name"] for i in range(len(pokemon["abilities"]))]
    pokemon_attributes["types"] = [pokemon["types"][i]["type"]["name"] for i in range(len(pokemon["types"]))]
    pokemon_attributes["sprite"] = pokemon["sprites"]["front_default"]
    pokemon_attributes["level_caught"] = 19
    pokemon_attributes["weight"] = pokemon["weight"]
    pokemon_attributes["gender"] = "male"

    # evolution

    # 'https://pokeapi.co/api/v2/evolution-chain/67/'
    chain_id = pokemon_species["evolution_chain"]["url"].split("/")[-2]
    chain = requests.get(f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/").json()

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
    pokemon_attributes["evolution_data"] = []


    if(len(chain["chain"]["evolves_to"]) > 0):
        # stage 1 --> stage 2
        if(str(chain["chain"]["species"]["name"]) == str(pokemon_attributes["name"])):
            for evo in chain["chain"]["evolves_to"]:
                pokemon_attributes["evolution_data"].append({
                    "evolves_to": {
                        "species": evo["species"]["name"],
                        "evolution_details": [{"min_level": evo["evolution_details"][0]["min_level"]}, {"trigger": {"name": evo["evolution_details"][0]["trigger"]["name"]}}]
                    }
                })
    # stage 2 --> stage 3
        if(str(chain["chain"]["evolves_to"][0]["species"]["name"]) == str(pokemon_attributes["name"])):
            for evo in chain["chain"]["evolves_to"][0]["evolves_to"]:
                pokemon_attributes["evolution_data"].append({
                    "evolves_to": {
                        "species": evo["species"]["name"],
                        "evolution_details": [{"min_level": evo["evolution_details"][0]["min_level"]}, {"trigger": {"name": evo["evolution_details"][0]["trigger"]["name"]}}]
                    }
                })

    # pretty print json data
    json_formatted_str = json.dumps(pokemon_attributes, indent=2)
    print(json_formatted_str)

    return pokemon_attributes



# compare the speed of direct requests vs pokebase wrapper
# requests is faster by 7000%... 
def compare_api_speeds(pokemon_name: str, num_trials: int = 5) -> dict:
    """
    Compare the speed of direct requests vs pokebase wrapper
    Returns a dictionary with timing results
    """
    results = {
        "pokebase_times": [],
        "requests_times": [],
        "pokebase_avg": 0,
        "requests_avg": 0,
        "faster_method": "",
        "speed_difference": 0
    }
    
    print(f"Testing {num_trials} trials for '{pokemon_name}'...")
    
    # Test pokebase wrapper
    for i in range(num_trials):
        start_time = time.time()
        try:
            pokemon = pb.pokemon(pokemon_name.lower())
            pokemon_species = pb.pokemon_species(pokemon.name.lower())
            # Access some attributes to ensure full loading
            _ = pokemon.name, pokemon.id, pokemon_species.evolution_chain
        except Exception as e:
            print(f"Pokebase error on trial {i+1}: {e}")
            continue
        end_time = time.time()
        results["pokebase_times"].append(end_time - start_time)
    
    # Test direct requests
    for i in range(num_trials):
        start_time = time.time()
        try:
            response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}")
            response.raise_for_status()
            pokemon_data = response.json()
            
            # Get species data
            species_url = pokemon_data["species"]["url"]
            species_response = requests.get(species_url)
            species_response.raise_for_status()
            species_data = species_response.json()
            
            # Get evolution chain data
            evolution_url = species_data["evolution_chain"]["url"]
            evolution_response = requests.get(evolution_url)
            evolution_response.raise_for_status()
            evolution_data = evolution_response.json()
            
        except Exception as e:
            print(f"Requests error on trial {i+1}: {e}")
            continue
        end_time = time.time()
        results["requests_times"].append(end_time - start_time)
    
    # Calculate averages
    if results["pokebase_times"]:
        results["pokebase_avg"] = sum(results["pokebase_times"]) / len(results["pokebase_times"])
    if results["requests_times"]:
        results["requests_avg"] = sum(results["requests_times"]) / len(results["requests_times"])
    
    # Determine which is faster
    if results["pokebase_avg"] < results["requests_avg"]:
        results["faster_method"] = "pokebase"
        results["speed_difference"] = results["requests_avg"] - results["pokebase_avg"]
    else:
        results["faster_method"] = "requests"
        results["speed_difference"] = results["pokebase_avg"] - results["requests_avg"]
    
    return results


def print_comparison_results(results: dict):
    """Print formatted comparison results"""
    print("\n" + "="*50)
    print("API SPEED COMPARISON RESULTS")
    print("="*50)
    print(f"Pokebase average time: {results['pokebase_avg']:.4f} seconds")
    print(f"Requests average time: {results['requests_avg']:.4f} seconds")
    print(f"Faster method: {results['faster_method'].upper()}")
    print(f"Speed difference: {results['speed_difference']:.4f} seconds")
    print(f"Pokebase times: {[f'{t:.4f}' for t in results['pokebase_times']]}")
    print(f"Requests times: {[f'{t:.4f}' for t in results['requests_times']]}")
    print("="*50)

def evolution_parse(index):
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
    pokemon_species = requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{index}").json()
    chain_id = pokemon_species["evolution_chain"]["url"].split("/")[-2]
    chain = requests.get(f"https://pokeapi.co/api/v2/evolution-chain/{chain_id}/").json()
    data = {"name": pokemon_species["name"], "evolution_data": []}

    print(2)
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


