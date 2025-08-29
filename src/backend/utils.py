import requests

BW_LOCATIONS_ORDERED = ["Nuvema Town", "Juniper's Lab", "Route 1", "Accumula Town", "Route 2", "Striaton City", "The Dreamyard", "Striaton Gym",
                           "Route 3", "Wellspring Cave", "Nacrene City", "Nacrene Gym", "Pinwheel Forest", "Skyarrow Bridge", "Castelia City", "Castelia Gym",
                           "Route 4", "Desert Resort", "Relic Castle", "Nimbasa City", "Nimbasa Gym", "Anville Town", "Route 5", "Driftveil Drawbridge", "Driftveil City", "Cold Storage", "Driftveil Gym",
                           "Route 6", "Chargestone Cave", "Mistralton City", "Route 7", "Celestial Tower", "Mistralton Gym", "Route 17", "Route 18", "P2 Laboratory", "Mistralton Cave", "Rumination Field",
                           "Twist Mountain", "Icirrus City", "Icirrus Gym", "Dragonspiral Tower", "Relic Castle", "Nacrene Museum", "Route 8", "Moor of Icirrus", "Tubeline Bridge", "Route 9",
                           "Opelucid City", "Opelucid Gym", "Route 10", "Victory Road", "Opelucid City", "Opelucid Gym", "Victory Road",
                           "Nuvema Town", "The Dreamyard", "The Royal Unova", "Relic Castle", "Nimbasa City", "Driftveil City", "Chargestone Cave", "Twist Mountain", "Challenger's Cave", "Opelucid City",
                           "Route 11", "Village Bridge", "Route 12", "Lacunosa Town", "Route 13", "Giant Chasm", "Undella Town", "Undella Bay", "Abyssal Ruins", "Route 14", "Abundant Shrine",
                           "Black City", "White Forest", "Route 15", "Poké Transfer Lab", "Marvelous Bridge", "Route 16", "Lostlorn Forest"
                           ]

BW2_LOCATIONS_ORDERED = ["Aspertia City", "Route 19", "Floccesy Town", "Route 20", "Floccesy Ranch", "Pledge Grove", "Aspertia Gym",
                        "Virbank City", "Virbank Complex", "Virbank Gym", "Pokéstar Studios", "Castelia City", "Castelia Sewers", "Castelia Gym",
                        "Route 4", "Desert Resort", "Relic Castle", "Join Avenue", "Nimbasa City", "Nimbasa Gym", "Anville Town", "Route 16", "Lostlorn Forest"
                        "Route 5", "Driftveil Drawbridge", "Driftveil City", "Driftveil Gym", "Pokémon World Tournament", "Plasma Frigate", "Relic Passage"
                        "Route 6", "Mistralton Cave", "Chargestone Cave", "Mistralton City", "Route 7", "Celestial Tower", "Mistralton Gym"
                        "Lentimas Town", "Strange House", "Reversal Mountain", "Undella Town", "Undella Bay", "Route 13", "Lacunosa Town", "Route 12", "Village Bridge", "Route 11"
                        "Opelucid City", "Route 9", "Opelucid Gym", "Marine Tube", "Humilau City", "Humilau Gym", "Route 22", "Route 21", "Seaside Cave", "Plasma Frigate", "Giant Chasm"
                        "Route 23", "Victory Road", "The Pokémon League"]



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
        if cleaned_locations.__contains__(loc_lower):
            continue
        
        # Handle route prefix
        if loc_lower.startswith("route"):
            loc_lower = loc_lower.replace("route", region.lower() + "-route")
       

        # Apply all replacements at once using translate
        cleaned_loc = loc_lower.translate(translation_table)

        # check if location contains pokemon
        if requests.get(f"https://pokeapi.co/api/v2/location-area/{cleaned_loc}-area").status_code != 200:
                continue

        cleaned_locations.append(cleaned_loc)
        print(cleaned_loc)

    return cleaned_locations



def get_region_locations(region: str) -> list[str]:
    reg = requests.get(f"https://pokeapi.co/api/v2/region/{region.lower()}").json()
    locations = []
    for loc in reg["locations"]:
         locations.append(loc["name"])
    return locations




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

def get_encounters(route: str, version: str) -> list[list]:
    route_area = requests.get(f"https://pokeapi.co/api/v2/location-area/{route.lower()}").json()
    try:
        encounters = route_area["pokemon_encounters"]
    except:
        return Exception("Location contains no encounters")


    encounter_data = []
    for encounter in encounters:
        for version in encounter["version_details"]:
            if version["version"]["name"] == version:
                name = encounter["pokemon"]["name"]
                min_level = 0
                max_level = 100
                for details in version["encounter_details"]:
                    if(min_level > details["min_level"]):
                        min_level = details["min_level"]
                    if(max_level < details["max_level"]):
                        max_level = details["max_level"]
                encounter_data.append([name, min_level, max_level, version])
    if encounter_data == []:
        return Exception("Location contains no encounters")

    return encounter_data
