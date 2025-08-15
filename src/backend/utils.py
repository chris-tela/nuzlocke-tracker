import requests

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
        # check if location contains pokemon
        else:
            if requests.get(f"https://pokeapi.co/api/v2/location-area/{loc_lower}-area").status_code != 200:
                continue
        # Apply all replacements at once using translate
        cleaned_loc = loc_lower.translate(translation_table)
        cleaned_locations.append(cleaned_loc)
        print(cleaned_loc)

    return cleaned_locations






