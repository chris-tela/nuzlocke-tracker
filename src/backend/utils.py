import requests
import re
BW_LOCATIONS_ORDERED = ["Nuvema Town", "Juniper's Lab", "Route 1", "Accumula Town", "Route 2", "Striaton City", "The Dreamyard", "Striaton Gym",
                           "Route 3", "Wellspring Cave", "Nacrene City", "Nacrene Gym", "Pinwheel Forest", "Skyarrow Bridge", "Castelia City", "Castelia Gym",
                           "Route 4", "Desert Resort", "Relic Castle", "Nimbasa City", "Nimbasa Gym", "Anville Town", "Route 5", "Driftveil Drawbridge", "Driftveil City", "Cold Storage", "Driftveil Gym",
                           "Route 6", "Chargestone Cave", "Mistralton City", "Route 7", "Celestial Tower", "Mistralton Gym", "Route 17", "Route 18", "P2 Laboratory", "Mistralton Cave", "Rumination Field",
                           "Twist Mountain", "Icirrus City", "Icirrus Gym", "Dragonspiral Tower", "Nacrene Museum", "Route 8", "Moor of Icirrus", "Tubeline Bridge", "Route 9",
                           "Opelucid City", "Opelucid Gym", "Route 10", "Victory Road", "Opelucid City", "Opelucid Gym", "Victory Road",
                           "Nuvema Town", "The Dreamyard", "The Royal Unova", "Nimbasa City", "Driftveil City", "Twist Mountain", "Challenger's Cave", "Opelucid City",
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

RUBYSAPPHIRE_LOCATIONS_ORDERED = ["Littleroot Town", "Route 101", "Oldale Town", "Route 103 (West)", "Route 102", "Petalburg City", "Route 104", "Petalburg Woods",
"Rustboro City", "Rustboro Gym", "Route 116", "Rusturf Tunnel", "Route 105", "Route 106", "Dewford Town", "Dewford Gym", "Granite Cave", "Route 107", "Route 108",
"Route 109", "Slateport City", "Oceanic Museum", "Route 110", "Trick House", "Mauville City", "Mauville Gym", "Route 117", "Verdanturf Town", "Rusturf Tunnel (Revisited)",
"Route 111 (South)", "Route 112 (South)", "Fiery Path", "Route 112 (North)", "Route 111 (North)", "Route 113", "Fallarbor Town", "Route 114", "Meteor Falls", "Route 115",
"Route 112 (South, Revisited)", "Mt. Chimney", "Jagged Pass", "Lavaridge Town", "Lavaridge Gym", "Route 111 (Desert)", "Petalburg Gym", "New Mauville", "Route 118",
"Route 119", "Weather Institute", "Fortree City", "Fortree Gym", "Route 120", "Scorched Slab", "Route 121", "Safari Zone", "Route 122", "Mt. Pyre", "Route 123",
"Slateport Harbor", "Lilycove City", "Team Magma Hideout/Team Aqua Hideout", "Route 124", "Mossdeep City", "Mossdeep Gym", "Route 125", "Shoal Cave", "Route 127",
"Route 128", "Seafloor Cavern", "Route 126", "Sootopolis City", "Cave of Origin", "Sootopolis Gym", "Route 129", "Route 130", "Mirage Island", "Route 131", "Pacifidlog Town",
"Route 132", "Route 133", "Route 134", "Sealed Chamber", "Route 105", "Island Cave", "Route 107", "Route 108", "Abandoned Ship", "Desert Ruins", "Ancient Tomb",
"Ever Grande City", "Victory Road", "The Pokémon League", "S.S. Tidal", "Battle Tower", "Sky Pillar"]

EMERALD_LOCATIONS_ORDERED = ["Littleroot Town", "Route 101", "Oldale Town", "Route 103", "Route 102", "Petalburg City", "Route 104", "Petalburg Woods", "Rustboro City", "Rustboro Gym", "Route 116", "Rusturf Tunnel",
"Route 105", "Route 106", "Dewford Town", "Dewford Gym", "Granite Cave", "Route 107", "Route 108", "Route 109", "Slateport City", "Oceanic Museum", "Route 110", "Trick House",
"Mauville City", "Mauville Gym", "Route 117", "Verdanturf Town", "Rusturf Tunnel (Revisited)", "Route 111 (South)", "Route 112 (South)", "Fiery Path", "Route 112 (North)", "Route 111 (North)", "Route 113", "Fallarbor Town", "Route 114",
"Meteor Falls", "Route 115", "Mt. Chimney", "Jagged Pass", "Lavaridge Town", "Lavaridge Gym", "Route 111 (Desert)", "Mirage Tower", "Petalburg Gym", "Route 115", "Route 105", "Route 107", "Route 108",
"Abandoned Ship","New Mauville", "Route 118", "Route 119","Weather Institute", "Fortree City","Route 120", "Fortree Gym", "Route 121", "Safari Zone", "Route 122",
"Mt. Pyre","Route 123", "Jagged Pass", "Team Magma Hideout", "Slateport City", "Lilycove City", "Team Aqua Hideout",
"Route 124", "Mossdeep City", "Space Center", "Route 125", "Shoal Cave","Route 127", "Route 128", "Seafloor Cavern",
"Route 126", "Sootopolis City", "Cave of Origin", "Route 129", "Route 130", "Route 131", "Pacifidlog Town",
"Route 132", "Route 133", "Route 13", "Desert Ruins", "Island Cave", "Ancient Tomb", "Sky Pillar", "Sootopolis City",
"Sky Pillar", "Ever Grande City", "Victory Road", "The Pokémon League",
"Littleroot Town", "Safari Zone", "Altering Cave", "Desert Underpass","Terra Cave","Marine Cave", "Meteor Falls","Trainer Hill"]



 
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

        # might not be needed; sometimes games revisit routes in the walkthrough with new "access" gained
        # if cleaned_locations.__contains__(loc_lower):
        #     continue
        
        # if string contains parantheses, remove it
        if loc_lower.__contains__("(") and loc_lower.__contains__(")"):
            loc_lower = re.sub(r"\(.*?\)", "", loc_lower)
        # Handle route prefix
        if loc_lower.startswith("route"):
            loc_lower = loc_lower.replace("route", region.lower() + "-route")
       
        if loc_lower.endswith(" "):
            loc_lower = loc_lower[:-1]
        # Apply all replacements at once using translate
        cleaned_loc = loc_lower.translate(translation_table)

        # check if location contains pokemon
        # if requests.get(f"https://pokeapi.co/api/v2/location-area/{cleaned_loc}-area").status_code != 200:
        #         continue

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

def get_encounters(route: str, region_name: str, version_name: str) -> list[list]:
    # check if location area exists, if not, check if location exists, otherwise return function
    # TODO: Deprecate
    if route.startswith(version_name + "-route"):
        route = route.replace(version_name, region_name)
        route += "-area"

    if route.startswith(region_name + "-route"):
        route += "-area"

    try:
        route_area = requests.get(f"https://pokeapi.co/api/v2/location-area/{route.lower()}").json()
    except Exception as e:
        try:
            return get_location(route, region_name,version_name)
        except Exception as e:
            print(route + "2")
            raise Exception("Location contains no encounters")
        
            

    try:
        encounters = route_area["pokemon_encounters"]
    except:
        print(route + "1")
        raise Exception("Location contains no encounters")


    encounter_data = []
    for encounter in encounters:
        for version in encounter["version_details"]:
            if version["version"]["name"] == version_name:
                name = encounter["pokemon"]["name"]
                min_level = 100
                max_level = 1
                for details in version["encounter_details"]:
                    if(min_level > details["min_level"]):
                        min_level = details["min_level"]
                    if(max_level < details["max_level"]):
                        max_level = details["max_level"]
                encounter_data.append([name, min_level, max_level, version_name, region_name])
    if encounter_data == []:
        print(route + "3")
        raise Exception("Location contains no encounters")

    return encounter_data

'''
function is used when a location has multiple areas, all containing encounters that need to be condensed into a single area that isn't in the location-area api
used as a 'helper' for get_encounters
'''
def get_location(location: str, region: str,  version: str) -> list[list]:
    location = requests.get(f"https://pokeapi.co/api/v2/location/{location.lower()}").json()
    try:
        areas = location["areas"]
    except areas is None:
        raise Exception("Location contains no areas")
    
    if len(areas) <= 1:
        raise Exception("Location contains one or none areas, and does not need to be condensed")
    

    areas_encounters = []
    for area in areas:
        try:
            area_encounter = get_encounters(area["name"], region, version)
            areas_encounters.append(area_encounter)
        except Exception as e:
            continue



    if len(areas_encounters) == 0:
        raise Exception()
    # condense areas_encounters into a single list
    # iterate through each pokemon, find its min and max level across all areas and add to condensed_encounters

    '''
    [[[pokemon, min, max, version], [pokemon, min, max, version]], ]]
    '''
    condensed_encounters = []
    pokemon_list = []
    for x in range(len(areas_encounters)):
        for y in range(len(areas_encounters[x])):
            pokemon = areas_encounters[x][y][0]
            if pokemon not in pokemon_list:
                pokemon_list.append(pokemon)
                min_level = areas_encounters[x][y][1]
                max_level = areas_encounters[x][y][2]
                condensed_encounters.append([pokemon, min_level, max_level, version, region])

            else:
                # get data for pokemon from condensed_encounters
                for z in range(len(condensed_encounters)):
                    if condensed_encounters[z][0] == pokemon:
                        min_level = condensed_encounters[z][1]
                        max_level = condensed_encounters[z][2]
                        if min_level > areas_encounters[x][y][1]:
                            min_level = areas_encounters[x][y][1]
                        if max_level < areas_encounters[x][y][2]:
                            max_level = areas_encounters[x][y][2]
                        condensed_encounters.pop(z)
                        condensed_encounters.append([pokemon, min_level, max_level, version, region])
                        break
    print(condensed_encounters)
    return condensed_encounters






