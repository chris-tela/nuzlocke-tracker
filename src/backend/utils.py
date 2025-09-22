import requests
import re

# locations orderd in a playthrough format (scraped from bulbapedia)

YELLOW_LOCATIONS_ORDERED = ["Pallet Town", "Route 1", "Viridian City", "Pallet Town (revisited)", "Route 2 (West)",
"Viridian Forest", "Pewter City", "Pewter Gym", "Route 3", "Mt. Moon", "Route 4", "Cerulean City", "Cerulean Gym", "Route 24", "Route 25", "Route 5",
"Route 6", "Vermilion City", "S.S. Anne", "Vermilion Gym", "Route 11", "Diglett's Cave", "Route 2 (East)", "Pewter Museum of Science", "Route 9", "Route 10 (North)",
"Rock Tunnel", "Route 10 (South)", "Lavender Town", "Route 8", "Route 7",
"Celadon City", "Celadon Gym", "Rocket Hideout", "Pokémon Tower", "Saffron City", "Silph Co.", "Saffron Gym",
"Route 16", "Route 17", "Route 18", "Fuchsia City", "Fuchsia Gym", "Safari Zone", "Route 12", "Route 13", "Route 14", "Route 15", "Route 19", "Route 20 (East)", "Seafoam Islands", "Route 20 (West)",
"Cinnabar Island", "Pokémon Lab", "Pokémon Mansion", "Cinnabar Gym", "Route 21", "Power Plant", "Viridian Gym",
"Route 22", "Route 23", "Victory Road", "Indigo Plateau", "Cerulean Cave"]

RED_BLUE_LOCATIONS_ORDERED = ["Pallet Town", "Route 1", "Viridian City", "Pallet Town (Revisited)", "Route 2 (West)",
"Viridian Forest", "Pewter City", "Pewter Gym", "Route 3","Mt. Moon", "Route 4", "Cerulean City", "Cerulean Gym", "Route 24", "Route 25", "Route 5", "Route 6",
"Vermilion City", "S.S. Anne", "Vermilion Gym", "Route 11", "Diglett's Cave", "Route 2 (East)", "Pewter Museum of Science","Route 9", "Route 10 (North)",
"Rock Tunnel", "Route 10 (South)", "Lavender Town", "Route 8", "Underground Path (Routes 7-8)","Route 7",
"Celadon City", "Celadon Gym","Rocket Hideout", "Pokémon Tower", "Saffron City", "Silph Co.", "Saffron Gym",
"Route 16","Route 17", "Route 18", "Fuchsia City", "Fuchsia Gym", "Safari Zone", "Route 12", "Route 13", "Route 14", "Route 15", "Route 19", "Route 20 (East)", "Seafoam Islands", "Route 20 (West)",
"Cinnabar Island", "Pokémon Lab", "Pokémon Mansion", "Cinnabar Gym", "Route 21", "Power Plant", "Viridian Gym",
"Route 22", "Route 23", "Victory Road", "Indigo Plateau", "Cerulean Cave"]

FIRERED_LEAFGREEN_LOCATIONS_ORDERED = ["Pallet Town", "Route 1", "Viridian City", "Pallet Town (Revisited)", "Route 2 (West)", "Viridian Forest", "Pewter City", "Pewter Gym",
"Route 3", "Mt. Moon", "Route 4", "Cerulean City", "Cerulean Gym", "Route 24", "Route 25", "Route 5", "Route 6", "Vermilion City", "S.S. Anne", "Vermilion Gym",
"Route 11", "Diglett's Cave", "Route 2 (East)", "Pewter Museum of Science", "Route 9", "Route 10 (North)",
"Rock Tunnel", "Route 10 (South)", "Lavender Town", "Route 8", "Route 7", "Celadon City","Celadon Gym", "Rocket Hideout", "Pokémon Tower",
"Route 12", "Route 13", "Route 14", "Route 15", "Fuchsia City", "Fuchsia Gym", "Safari Zone", "Route 18", "Route 17", "Route 16",
"Saffron City", "Silph Co.", "Fighting Dojo", "Saffron Gym", "Route 19", "Route 20 (East)", "Seafoam Islands", "Route 20 (West)",
"Cinnabar Island", "Pokémon Lab", "Pokémon Mansion", "Cinnabar Gym", "Sevii Islands", "One Island", "Two Island", "Three Island",
"Route 21", "Power Plant", "Viridian Gym", "Route 22", "Route 23", "Victory Road", "Indigo Plateau", "Sevii Islands", "Four Island", "Six Island",
"Sevii Islands", "Five Island", "Seven Island", "Cerulean Cave"]

GOLD_SILVER_LOCATIONS_ORDERED = [
"New Bark Town", "Route 29","Route 46", "Cherrygrove City", "Route 30", "Mr. Pokémon's House","Professor Elm's Lab",
"Route 31", "Violet City", "Sprout Tower", "Violet Gym", "Route 32", "Ruins of Alph", "Union Cave", "Route 33",
"Azalea Town","Slowpoke Well", "Azalea Gym", "Ilex Forest", "Route 34", "Goldenrod City", "Goldenrod Gym",
"Route 35", "National Park","Route 36", "Route 37", "Ecruteak City", "Burned Tower", "Ecruteak Gym", "Route 38", "Route 39",
"Olivine City", "Route 40", "Route 41", "Cianwood City", "Cianwood Gym", "Olivine Gym", "Route 42", "Mt. Mortar",
"Mahogany Town", "Route 43", "Lake of Rage", "Rocket Hideout", "Mahogany Gym", "Goldenrod Radio Tower", "Goldenrod Underground", "Route 44", "Ice Path",
"Blackthorn City", "Blackthorn Gym", "Dragon's Den", "Route 45", "Dark Cave","Route 46", "Route 27", "Route 26", "Victory Road",
"Indigo Plateau", "S.S. Aqua", "Vermilion City", "Vermilion Gym", "Route 6", "Saffron City","Saffron Gym", "Route 8", "Lavender Town", 
"Route 10", "Rock Tunnel", "Route 9","Power Plant", "Cerulean City", "Route 24", "Route 25", "Cerulean Gym", "Route 5",
"Route 7", "Celadon City", "Celadon Gym", "Route 16", "Route 17", "Route 18", "Fuchsia City", "Fuchsia Gym",
"Route 15", "Route 14", "Route 13", "Route 12", "Route 11", "Diglett's Cave", "Route 2", "Pewter City", "Pewter Gym",
"Route 3", "Mt. Moon", "Route 4", "Viridian City", "Route 1", "Pallet Town", "Route 21", "Cinnabar Island", "Route 20", "Cinnabar Gym","Route 19",
"Viridian Gym", "Professor Oak's Lab", "Route 22", "Route 28", "Mt. Silver", "Tin Tower", "Whirl Islands", "Mt. Mortar (Revisited)"
]

CRYSTAL_LOCATIONS_ORDERED = ["New Bark Town", "Route 29", "Cherrygrove City", "Route 30", "Mr. Pokémon's House", "Professor Elm's Lab",
"Route 31", "Violet City", "Sprout Tower", "Violet Gym", "Route 32", "Ruins of Alph", "Union Cave", "Route 33",
"Azalea Town", "Slowpoke Well", "Azalea Gym", "Ilex Forest", "Route 34", "Goldenrod City", "Goldenrod Gym",
"Route 35", "National Park", "Route 36", "Route 37", "Ecruteak City", "Burned Tower", "Ecruteak Gym", "Route 38", "Route 39",
"Olivine City", "Route 40", "Route 41", "Cianwood City", "Cianwood Gym", "Olivine Gym", "Route 42", "Mt. Mortar",
"Mahogany Town", "Route 43", "Lake of Rage", "Rocket Hideout", "Mahogany Gym", "Goldenrod Radio Tower", "Goldenrod Underground", "Tin Tower (1F)", "Route 44", "Ice Path",
"Blackthorn City", "Blackthorn Gym", "Dragon's Den", "Route 45", "Dark Cave", "Route 46", "Route 27", "Route 26", "Victory Road",
"Indigo Plateau", "S.S. Aqua", "Vermilion City", "Vermilion Gym", "Route 6", "Saffron City", "Saffron Gym",
"Route 8", "Lavender Town", "Route 10", "Rock Tunnel", "Route 9", "Power Plant", "Cerulean City", "Route 24", "Route 25", "Cerulean Gym", "Route 5",
"Route 7", "Celadon City", "Celadon Gym", "Route 16", "Route 17", "Route 18", "Fuchsia City", "Fuchsia Gym",
"Route 15", "Route 14", "Route 13", "Route 12", "Route 11", "Diglett's Cave", "Route 2", "Pewter City", "Pewter Gym",
"Route 3", "Mt. Moon", "Route 4", "Viridian City", "Route 1", "Pallet Town", "Route 21", "Cinnabar Island", "Route 20", "Cinnabar Gym", "Route 19",
"Viridian Gym", "Professor Oak's Lab", "Route 22", "Route 28", "Mt. Silver", "Tin Tower (Revisited)", "Whirl Islands", "Mt. Mortar (Revisited)"]

DIAMOND_PEARL_LOCATIONS_ORDERED = ["Twinleaf Town", "Verity Lakefront", "Lake Verity", "Route 201", "Sandgem Town", "Sandgem Beach", "Route 202", "Jubilife City", "Route 204", "Ravaged Path", "Route 203", "Oreburgh Gate", "Oreburgh City",
"Route 207", "Oreburgh Mine", "Oreburgh Gym", "Route 204 (South)", "Route 204 (North)", "Floaroma Town", "Route 205 (Parts 1-2)", "Valley Windworks", "Floaroma Meadow (South)", "Eterna Forest",
"Route 205 (Part 3)", "Eterna City", "Route 211 (West)", "Mt. Coronet (Northern Area Part 1)", "Eterna Gym", "Old Chateau", "Galactic Eterna Building", "Route 206", "Wayward Cave (Main part)", "Mt. Coronet (Southern Area Part 1)", "Route 208",
"Hearthome City", "Amity Square", "Route 209", "Lost Tower", "Solaceon Town", "Solaceon Ruins", "Route 210 (South)", "Route 215", "Veilstone City", "Veilstone Gym",
"Route 214", "Valor Lakefront", "Hotel Grand Lake", "Route 213", "Pastoria City", "Great Marsh", "Pastoria Gym", "Route 212", "Route 210 (North)", "Celestic Town", "Route 211 (East)", "Hearthome Gym",
"Fuego Ironworks", "Floaroma Meadow (North)", "Sandgem Beach", "Route 219", "Route 220", "Route 221", "Route 218", "Canalave City", "Iron Island", "Canalave Gym",
"Wayward Cave (Basement)", "Canalave Library", "Lake Valor", "Mt. Coronet (Northern Area Part 2)", "Route 216", "Route 217", "Acuity Lakefront", "Snowpoint City", "Snowpoint Gym", "Lake Acuity",
"Galactic HQ", "Galactic Warehouse", "Mt. Coronet (Southern Area Part 2)", "Mt. Coronet (Mountainside)", "Mt. Coronet (Upper Caverns)", "Spear Pillar", "Route 222", "Sunyshore City", "Vista Lighthouse",
"Sunyshore Gym", "Route 223", "Sinnoh Victory Road", "Sinnoh Pokémon League", "Twinleaf Town", "Pokémon Research Lab", "Route 224", "Pokémon Mansion", "Fullmoon Island", 
"Survival Area", "Route 226", "Route 227", "Stark Mountain", "Route 228", "Route 229", "Resort Area", "Route 230"]

PLATINUM_LOCATIONS_ORDERED = ["Twinleaf Town", "Route 201", "Lake Verity", "Sandgem Town", "Route 202", "Jubilife City", "Route 203", "Oreburgh Gate", "Oreburgh City", "Oreburgh Mine",
"Oreburgh Gym", "Jubilife City", "Route 204 (south)", "Ravaged Path", "Route 204 (north)", "Floaroma Town", "Floaroma Meadow", "Valley Windworks", "Route 205 (south)", "Eterna Forest", "Route 205 (east)", "Eterna City", "Eterna Gym",
"Eterna City", "Old Chateau", "Route 206", "Wayward Cave", "Route 207", "Mt. Coronet (south)", "Route 208", "Hearthome City", "Hearthome Gym", "Route 209",
"Solaceon Town", "Solaceon Ruins", "Lost Tower", "Route 210 (south)", "Route 215", "Veilstone City", "Veilstone Gym", "Route 214", "Maniac Tunnel", "Valor Lakefront", "Route 213", "Pastoria City",
"Pastoria Gym", "Route 212", "Valor Lakefront", "Route 210", "Celestic Town", "Fuego Ironworks", "Route 213", "Route 219", "Route 220", "Route 221", "Route 218", "Canalave City",
"Iron Island", "Canalave Gym", "Canalave City", "Lake Valor", "Lake Verity", "Route 211", "Mt. Coronet (north)", "Route 216", "Route 217", "Acuity Lakefront", "Snowpoint City", "Snowpoint Gym", "Lake Acuity", "Veilstone City",
"Mt. Coronet (south)", "Spear Pillar", "Distortion World", "Sendoff Spring", "Lake Verity", "Lake Valor", "Lake Acuity", "Route 222", "Sunyshore City",
"Sunyshore Gym", "Route 223", "Pokémon League (south)", "Victory Road", "Pokémon League (north)", "Twinleaf Town", "Sandgem Town", "Eterna City", "Great Marsh",
"Trophy Garden", "Pal Park", "Fullmoon Island", "Snowpoint Temple", "Spear Pillar", "Turnback Cave", "Distortion World", "Victory Road", "Route 224",
"Fight Area", "Route 225", "Survival Area", "Route 226", "Route 227", "Stark Mountain", "Survival Area", "Stark Mountain", "Route 228", "Route 229", "Resort Area", "Route 230"]

HEARTGOLD_SOULSILVER_LOCATIONS_ORDERED = ["New Bark Town", "Route 29", "Cherrygrove City", "Route 30", "Mr. Pokémon's House", "Professor Elm's Lab",
"Route 31", "Violet City", "Sprout Tower", "Violet Gym", "Route 32", "Ruins of Alph", "Union Cave", "Route 33",
"Azalea Town", "Slowpoke Well", "Azalea Gym", "Ilex Forest", "Route 34", "Goldenrod City", "Goldenrod Gym",
"Route 35", "Pokéathlon Dome", "National Park", "Route 36", "Route 37", "Ecruteak City", "Burned Tower", "Ecruteak Gym", "Route 38", "Route 39",
"Olivine City", "Olivine Lighthouse", "Route 40", "Route 41", "Cianwood City", "Cianwood Gym", "Olivine Gym", "Route 42", "Mt. Mortar",
"Mahogany Town", "Route 43", "Lake of Rage", "Team Rocket HQ", "Mahogany Gym", "Goldenrod Radio Tower", "Goldenrod Tunnel", "Route 44", "Ice Path",
"Blackthorn City", "Blackthorn Gym", "Dragon's Den", "Route 45", "Dark Cave", "Route 46", "Ecruteak Dance Theater", "Bellchime Trail", "Bell Tower", "Whirl Islands",
"Route 27", "Route 26", "Victory Road", "Indigo Plateau", "S.S. Aqua", "Vermilion City", "Vermilion Gym", "Route 6", "Saffron City", "Saffron Gym",
"Route 8", "Lavender Town", "Route 10", "Rock Tunnel", "Route 9", "Power Plant", "Cerulean City", "Route 24", "Route 25", "Cerulean Gym", "Route 5",
"Route 7", "Celadon City", "Celadon Gym", "Route 16", "Route 17", "Route 18", "Fuchsia City", "Fuchsia Gym",
"Route 15", "Route 14", "Route 13", "Route 12", "Route 11", "Diglett's Cave", "Route 2", "Pewter City", "Pewter Gym",
"Route 3", "Mt. Moon", "Route 4", "Viridian City", "Route 1", "Pallet Town", "Route 21", "Cinnabar Island", "Route 20", "Cinnabar Gym", "Seafoam Islands", "Route 19",
"Viridian Gym", "Professor Oak's Lab", "Route 22", "Route 28", "Mt. Silver", "Cerulean Cave", "Oak's Lab", "Silph Co.", "Mr. Pokémon's house",
"Cliff Edge Gate", "Route 47", "Cliff Cave", "Embedded Tower", "Route 48", "Safari Zone Gate", "Safari Zone", "Frontier Access", "Battle Frontier"]

BLACK_WHITE_LOCATIONS_ORDERED = ["Nuvema Town", "Juniper's Lab", "Route 1", "Accumula Town", "Route 2", "Striaton City", "The Dreamyard", "Striaton Gym",
                           "Route 3", "Wellspring Cave", "Nacrene City", "Nacrene Gym", "Pinwheel Forest", "Skyarrow Bridge", "Castelia City", "Castelia Gym",
                           "Route 4", "Desert Resort", "Relic Castle", "Nimbasa City", "Nimbasa Gym", "Anville Town", "Route 5", "Driftveil Drawbridge", "Driftveil City", "Cold Storage", "Driftveil Gym",
                           "Route 6", "Chargestone Cave", "Mistralton City", "Route 7", "Celestial Tower", "Mistralton Gym", "Route 17", "Route 18", "P2 Laboratory", "Mistralton Cave", "Rumination Field",
                           "Twist Mountain", "Icirrus City", "Icirrus Gym", "Dragonspiral Tower", "Nacrene Museum", "Route 8", "Moor of Icirrus", "Tubeline Bridge", "Route 9",
                           "Opelucid City", "Opelucid Gym", "Route 10", "Victory Road", "Opelucid City", "Opelucid Gym", "Victory Road",
                           "Nuvema Town", "The Dreamyard", "The Royal Unova", "Nimbasa City", "Driftveil City", "Twist Mountain", "Challenger's Cave", "Opelucid City",
                           "Route 11", "Village Bridge", "Route 12", "Lacunosa Town", "Route 13", "Giant Chasm", "Undella Town", "Undella Bay", "Abyssal Ruins", "Route 14", "Abundant Shrine",
                           "Black City", "White Forest", "Route 15", "Poké Transfer Lab", "Marvelous Bridge", "Route 16", "Lostlorn Forest"
                           ]

BLACK_2_WHITE_2_LOCATIONS_ORDERED = ["Aspertia City", "Route 19", "Floccesy Town", "Route 20", "Floccesy Ranch", "Pledge Grove", "Aspertia Gym",
                        "Virbank City", "Virbank Complex", "Virbank Gym", "Pokéstar Studios", "Castelia City", "Castelia Sewers", "Castelia Gym",
                        "Route 4", "Desert Resort", "Relic Castle", "Join Avenue", "Nimbasa City", "Nimbasa Gym", "Anville Town", "Route 16", "Lostlorn Forest"
                        "Route 5", "Driftveil Drawbridge", "Driftveil City", "Driftveil Gym", "Pokémon World Tournament", "Plasma Frigate", "Relic Passage"
                        "Route 6", "Mistralton Cave", "Chargestone Cave", "Mistralton City", "Route 7", "Celestial Tower", "Mistralton Gym"
                        "Lentimas Town", "Strange House", "Reversal Mountain", "Undella Town", "Undella Bay", "Route 13", "Lacunosa Town", "Route 12", "Village Bridge", "Route 11"
                        "Opelucid City", "Route 9", "Opelucid Gym", "Marine Tube", "Humilau City", "Humilau Gym", "Route 22", "Route 21", "Seaside Cave", "Plasma Frigate", "Giant Chasm"
                        "Route 23", "Victory Road", "The Pokémon League"]

RUBY_SAPPHIRE_LOCATIONS_ORDERED = ["Littleroot Town", "Route 101", "Oldale Town", "Route 103 (West)", "Route 102", "Petalburg City", "Route 104", "Petalburg Woods",
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
def get_region_locations_ordered(location_list: str, region: str) -> list[str]:
    # Get the actual list from globals using the string name
    actual_location_list = globals().get(location_list)
    if actual_location_list is None:
        raise ValueError(f"Location list '{location_list}' not found in globals")
    
    location_list = actual_location_list

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

    print(route)
 
    if route.startswith(region_name + "-route") and not route.__contains__("area"):
        route += "-area"

    try:
        route_area = requests.get(f"https://pokeapi.co/api/v2/location-area/{route.lower()}").json()
    except Exception as e:
        # account for sea routes ex : johto-route-40-area --> johto-sea-route-40-area
        if route.__contains__("route") and not route.__contains__("-sea-"):
            sea_route = route[:len(region_name)] + "-sea" + route[len(region_name):]
            try:
                sea_encounters = get_encounters(sea_route, region_name, version_name)
                if(not sea_encounters is None):
                    return sea_encounters
            except Exception as e:
                    raise Exception("Location contains no encounters")
            return
        try:
            return get_location(route, region_name, version_name)
        except Exception as e:
            raise Exception("Location contains no encounters")
        
            
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
                for details in version["encounter_details"]:
                    if(min_level > details["min_level"]):
                        min_level = details["min_level"]
                    if(max_level < details["max_level"]):
                        max_level = details["max_level"]
                encounter_data.append([name, min_level, max_level, version_name, region_name])
    if encounter_data == []:
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
    return condensed_encounters




#print(get_encounters("kanto-route-19-area", "kanto", "red"))

