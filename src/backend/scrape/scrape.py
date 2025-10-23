import requests
from bs4 import BeautifulSoup
import json
import sys
import re

def scrape_trainers(url):
    """
    Scrape trainer information from Pokemon DB and return structured data
    """
    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML with Beautiful Soup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        trainers_data = []
        
        # Find all sections with h2 elements that have gym, elite4, or champion IDs
        all_sections = soup.find_all('h2', id=re.compile(r'(gym|elite4|champion)-\d+'))
        
        for section in all_sections:
            section_id = section.get('id', '')
            section_type = section_id.split('-')[0] if '-' in section_id else ''
            section_number = section_id.split('-')[1] if '-' in section_id else ''
            
            # Extract location from the header text
            location = section.get_text(strip=True)
            
            # Find trainer cards within this section
            # Look for trainer cards that come after this h2 element
            current = section.find_next_sibling()
            section_trainers = []
            
            while current:
                # Stop if we hit another h2 element (next section)
                if current.name == 'h2':
                    break
                
                # Look for trainer cards in this element
                trainer_cards = current.find_all('span', class_='infocard trainer-head')
                for card in trainer_cards:
                    trainer_data = extract_trainer_from_card(card)
                    if trainer_data:
                        trainer_data["location"] = location
                        section_trainers.append(trainer_data)
                
                current = current.find_next_sibling()
            
            # Add section trainers to the main list
            trainers_data.extend(section_trainers)
        
        # Sort trainers by section number (gyms first, then elite4, then champion)
        trainers_data.sort(key=lambda x: extract_section_number_from_location(x.get("location", "")))
        
        return trainers_data
        
    except Exception as e:
        print(f"Error scraping data: {e}")
        return []

def extract_section_number_from_location(location):
    """
    Extract section number from location text for sorting
    Priority: Gyms (1000+), Elite Four (2000+), Champion (3000+)
    """
    try:
        # Check for gym number
        gym_match = re.search(r'Gym #(\d+)', location)
        if gym_match:
            return 1000 + int(gym_match.group(1))
        
        # Check for elite four number
        elite4_match = re.search(r'Elite Four #(\d+)', location)
        if elite4_match:
            return 2000 + int(elite4_match.group(1))
        
        # Check for champion number
        champion_match = re.search(r'Champion #(\d+)', location)
        if champion_match:
            return 3000 + int(champion_match.group(1))
        
        # Check for generic elite four or champion
        if 'Elite Four' in location:
            return 2000
        if 'Champion' in location:
            return 3000
            
        return 9999  # Put other trainers at the end
    except:
        return 9999

def is_element_after(element, reference_element):
    """
    Check if an element comes after a reference element in the DOM
    """
    try:
        # Get all elements in the same parent
        parent = reference_element.parent
        if not parent:
            return False
        
        # Find the position of the reference element
        reference_pos = None
        element_pos = None
        
        for i, child in enumerate(parent.find_all(recursive=False)):
            if child == reference_element:
                reference_pos = i
            if child == element:
                element_pos = i
        
        # Return True if element comes after reference element
        if reference_pos is not None and element_pos is not None:
            return element_pos > reference_pos
        
        return False
        
    except Exception as e:
        print(f"Error checking element position: {e}")
        return False

def extract_trainer_from_card(card):
    """
    Extract trainer data from a trainer card using the specific CSS selectors
    """
    try:
        trainer_data = {
            "location": "",
            "trainer_name": "",
            "trainer_image": "",
            "badge_name": "",
            "badge_type": "",
            "pokemon": []
        }
        
        # Extract trainer name from <span class="ent-name">
        trainer_name_span = card.find('span', class_='ent-name')
        if trainer_name_span:
            trainer_data["trainer_name"] = trainer_name_span.get_text(strip=True)
        
        # Extract trainer image from <img class="img-fixed img-trainer-v#">
        trainer_img = card.find('img', class_=re.compile(r'img-fixed img-trainer-v\d+'))
        if trainer_img and trainer_img.get('src'):
            trainer_data["trainer_png"] = trainer_img['src']
        
        # Extract badge type from <span class="itype {type}">
        type_spans = card.find_all('span', class_=re.compile(r'itype'))
        for type_span in type_spans:
            # Extract the text content from the span
            badge_type = type_span.get_text(strip=True)
            if badge_type:
                trainer_data["badge_type"] = badge_type
                break
        
        # Extract badge name from the text content
        badge_match = re.search(r'(\w+)\s+Badge', card.get_text(), re.I)
        if badge_match:
            trainer_data["badge_name"] = badge_match.group(1) + " Badge"
        
        # Look for Pokemon data that belongs specifically to this trainer
        # Find Pokemon cards that are in the same container as this trainer card
        pokemon_data = []
        
        # Look for Pokemon cards in the same parent container
        parent_container = card.parent
        if parent_container:
            # Find Pokemon cards that are siblings of this trainer card
            pokemon_cards = parent_container.find_all('div', class_='infocard trainer-pkmn')
            
            # Only take Pokemon cards that come after this trainer card but before the next trainer card
            for pokemon_card in pokemon_cards:
                # Check if this Pokemon card comes after the trainer card
                if is_element_after(pokemon_card, card):
                    # Check if there's another trainer card between this trainer and the Pokemon
                    has_trainer_between = False
                    for trainer_card in parent_container.find_all('span', class_='infocard trainer-head'):
                        if (is_element_after(trainer_card, card) and 
                            is_element_after(pokemon_card, trainer_card)):
                            has_trainer_between = True
                            break
                    
                    # Only add Pokemon if there's no trainer between this trainer and the Pokemon
                    if not has_trainer_between:
                        pokemon_info = extract_pokemon_from_pokemon_card(pokemon_card)
                        if pokemon_info:
                            pokemon_data.append(pokemon_info)
        
        trainer_data["pokemon"] = pokemon_data
        
        return trainer_data
        
    except Exception as e:
        print(f"Error extracting trainer from card: {e}")
        return None

def extract_pokemon_from_pokemon_card(pokemon_card):
    """
    Extract Pokemon data from a single Pokemon card
    """
    try:
        # Find the data section
        data_section = pokemon_card.find('span', class_='infocard-lg-data text-muted')
        if not data_section:
            return None
        
        # Extract Pokemon name from <a class="ent-name">
        pokemon_name_link = data_section.find('a', class_='ent-name')
        if not pokemon_name_link:
            return None
        
        pokemon_name = pokemon_name_link.get_text(strip=True)
        
        # Extract Pokemon ID from first <small> element
        small_elements = data_section.find_all('small')
        pokemon_id = ""
        if small_elements:
            id_text = small_elements[0].get_text(strip=True)
            id_match = re.search(r'#(\d+)', id_text)
            if id_match:
                pokemon_id = id_match.group(1)
        
        # Extract level from second <small> element (Level X)
        level = ""
        if len(small_elements) >= 2:
            level_text = small_elements[1].get_text(strip=True)
            level_match = re.search(r'Level (\d+)', level_text)
            if level_match:
                level = level_match.group(1)
        
        pokemon_data = {
            "name": pokemon_name,
            "id": pokemon_id,
            "level": level
        }
        
        return pokemon_data
        
    except Exception as e:
        print(f"Error extracting Pokemon from Pokemon card: {e}")
        return None

def extract_level_from_text(text):
    """
    Extract Pokemon level from text using regex
    """
    level_match = re.search(r'Lv\.?\s*(\d+)', text, re.I)
    if level_match:
        return int(level_match.group(1))
    return ""

def save_to_json(data, game_name):
    """
    Save trainer data to JSON file
    """
    try:
        filename = f"trainer_data/{game_name}_trainers.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    url = "https://pokemondb.net/red-blue/gymleaders-elitefour"
    if len(sys.argv) > 1:
        url = sys.argv[1]

    game_name = url.split("/")[-2]
    
    print(f"Scraping data from: {url}")
    trainers_data = scrape_trainers(url)
    
    if trainers_data:
        print(f"Found {len(trainers_data)} trainers")
        save_to_json(trainers_data, game_name)
        
        # Print first trainer as example
        if trainers_data:
            print("\nFirst trainer data:")
            print(json.dumps(trainers_data[0], indent=2))
    else:
        print("No trainer data found. The HTML structure might be different than expected.")

