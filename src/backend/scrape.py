
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
        
        # Find all gym sections with h2 elements that have gym IDs
        gym_sections = soup.find_all('h2', id=re.compile(r'gym-\d+'))
        
        for gym_section in gym_sections:
            gym_id = gym_section.get('id', '')
            gym_number = gym_id.replace('gym-', '') if gym_id else ''
            
            # Extract location from the header text
            location = gym_section.get_text(strip=True)
            
            # Find trainer cards within this gym section
            # Look for trainer cards that come after this h2 element
            current = gym_section.find_next_sibling()
            gym_trainers = []
            
            while current:
                # Stop if we hit another h2 element (next gym)
                if current.name == 'h2':
                    break
                
                # Look for trainer cards in this element
                trainer_cards = current.find_all('span', class_='infocard trainer-head')
                for card in trainer_cards:
                    trainer_data = extract_trainer_from_card(card)
                    if trainer_data:
                        trainer_data["location"] = location
                        gym_trainers.append(trainer_data)
                
                current = current.find_next_sibling()
            
            # Add gym trainers to the main list
            trainers_data.extend(gym_trainers)
        
        # Sort trainers by gym number
        trainers_data.sort(key=lambda x: extract_gym_number_from_location(x.get("location", "")))
        
        return trainers_data
        
    except Exception as e:
        print(f"Error scraping data: {e}")
        return []

def extract_gym_number_from_location(location):
    """
    Extract gym number from location text for sorting
    """
    try:
        match = re.search(r'Gym #(\d+)', location)
        if match:
            return int(match.group(1))
        return 999  # Put non-gym trainers at the end
    except:
        return 999

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
            "trainer name": "",
            "trainer.png": "",
            "badge name": "",
            "badge type": "",
            "pokemon": []
        }
        
        # Extract trainer name from <span class="ent-name">
        trainer_name_span = card.find('span', class_='ent-name')
        if trainer_name_span:
            trainer_data["trainer name"] = trainer_name_span.get_text(strip=True)
        
        # Extract trainer image from <img class="img-fixed img-trainer-v11">
        trainer_img = card.find('img', class_='img-fixed img-trainer-v11')
        if trainer_img and trainer_img.get('src'):
            trainer_data["trainer.png"] = trainer_img['src']
        
        # Extract badge type from <span class="itype {type}">
        type_spans = card.find_all('span', class_=re.compile(r'itype'))
        for type_span in type_spans:
            # Extract the text content from the span
            badge_type = type_span.get_text(strip=True)
            if badge_type:
                trainer_data["badge type"] = badge_type
                break
        
        # Extract badge name from the text content
        badge_match = re.search(r'(\w+)\s+Badge', card.get_text(), re.I)
        if badge_match:
            trainer_data["badge name"] = badge_match.group(1) + " Badge"
        
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

def extract_pokemon_from_card(card):
    """
    Extract Pokemon data from the trainer card itself
    """
    pokemon_list = []
    
    try:
        # Look for Pokemon links in the card
        pokemon_links = card.find_all('a', href=re.compile(r'pokemon', re.I))
        
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                # Try to find level in the same element or nearby
                level = extract_level_from_text(link.parent.get_text())
                
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",  # Would need Pokemon ID lookup
                    "level": level
                }
                pokemon_list.append(pokemon_data)
        
        return pokemon_list
        
    except Exception as e:
        print(f"Error extracting Pokemon from card: {e}")
        return []

def parse_pokemondb_gym_leaders(soup):
    """
    Parse gym leaders from Pokemon DB structure
    """
    trainers = []
    
    try:
        # Look for gym leader sections
        gym_sections = soup.find_all(['h2', 'h3'], string=re.compile(r'gym.*#\d+', re.I))
        
        for section in gym_sections:
            # Get the gym number and city
            gym_text = section.get_text()
            gym_match = re.search(r'Gym #(\d+),?\s*(.+)', gym_text, re.I)
            if gym_match:
                gym_num = gym_match.group(1)
                city = gym_match.group(2).strip()
                
                # Find trainer data in the following content
                trainer_data = extract_gym_leader_data(section, city, gym_num)
                if trainer_data:
                    trainers.extend(trainer_data)
        
        return trainers
        
    except Exception as e:
        print(f"Error parsing Pokemon DB gym leaders: {e}")
        return []

def parse_pokemondb_elite_four(soup):
    """
    Parse elite four from Pokemon DB structure
    """
    trainers = []
    
    try:
        # Look for elite four sections
        elite_sections = soup.find_all(['h2', 'h3'], string=re.compile(r'elite four', re.I))
        
        for section in elite_sections:
            # Find trainer data in the following content
            trainer_data = extract_elite_four_data(section)
            if trainer_data:
                trainers.extend(trainer_data)
        
        return trainers
        
    except Exception as e:
        print(f"Error parsing Pokemon DB elite four: {e}")
        return []

def parse_pokemondb_other_trainers(soup):
    """
    Parse other trainers from Pokemon DB structure
    """
    trainers = []
    
    try:
        # Look for other trainer sections
        other_sections = soup.find_all(['h2', 'h3'], string=re.compile(r'other trainers', re.I))
        
        for section in other_sections:
            # Find trainer data in the following content
            trainer_data = extract_other_trainer_data(section)
            if trainer_data:
                trainers.extend(trainer_data)
        
        return trainers
        
    except Exception as e:
        print(f"Error parsing Pokemon DB other trainers: {e}")
        return []

def extract_gym_leader_data(section, city, gym_num):
    """
    Extract gym leader data from a section
    """
    trainers = []
    
    try:
        # Find the next sibling elements that contain trainer data
        current = section.find_next_sibling()
        
        while current:
            # Look for trainer names and Pokemon data
            trainer_name = extract_trainer_name_from_element(current)
            if trainer_name:
                pokemon_data = extract_pokemon_from_element(current)
                badge_data = extract_badge_from_element(current)
                
                trainer_data = {
                    "location": city,
                    "trainer name": trainer_name,
                    "trainer.png": "",
                    "badge name": badge_data.get("name", ""),
                    "badge type": badge_data.get("type", ""),
                    "pokemon": pokemon_data
                }
                trainers.append(trainer_data)
            
            # Move to next sibling
            current = current.find_next_sibling()
            
            # Stop if we hit another major section
            if current and current.name in ['h2', 'h3']:
                break
        
        return trainers
        
    except Exception as e:
        print(f"Error extracting gym leader data: {e}")
        return []

def extract_elite_four_data(section):
    """
    Extract elite four data from a section
    """
    trainers = []
    
    try:
        # Find the next sibling elements that contain trainer data
        current = section.find_next_sibling()
        
        while current:
            # Look for trainer names and Pokemon data
            trainer_name = extract_trainer_name_from_element(current)
            if trainer_name:
                pokemon_data = extract_pokemon_from_element(current)
                
                trainer_data = {
                    "location": "Elite Four",
                    "trainer name": trainer_name,
                    "trainer.png": "",
                    "badge name": "",
                    "badge type": "",
                    "pokemon": pokemon_data
                }
                trainers.append(trainer_data)
            
            # Move to next sibling
            current = current.find_next_sibling()
            
            # Stop if we hit another major section
            if current and current.name in ['h2', 'h3']:
                break
        
        return trainers
        
    except Exception as e:
        print(f"Error extracting elite four data: {e}")
        return []

def extract_other_trainer_data(section):
    """
    Extract other trainer data from a section
    """
    trainers = []
    
    try:
        # Find the next sibling elements that contain trainer data
        current = section.find_next_sibling()
        
        while current:
            # Look for trainer names and Pokemon data
            trainer_name = extract_trainer_name_from_element(current)
            if trainer_name:
                pokemon_data = extract_pokemon_from_element(current)
                
                trainer_data = {
                    "location": "",
                    "trainer name": trainer_name,
                    "trainer.png": "",
                    "badge name": "",
                    "badge type": "",
                    "pokemon": pokemon_data
                }
                trainers.append(trainer_data)
            
            # Move to next sibling
            current = current.find_next_sibling()
            
            # Stop if we hit another major section
            if current and current.name in ['h2', 'h3']:
                break
        
        return trainers
        
    except Exception as e:
        print(f"Error extracting other trainer data: {e}")
        return []

def extract_trainer_name_from_element(element):
    """
    Extract trainer name from an element
    """
    try:
        # Look for bold text that might be trainer names
        bold_elements = element.find_all(['b', 'strong'])
        for bold in bold_elements:
            text = bold.get_text(strip=True)
            if text and len(text) > 1 and not text.isdigit():
                # Clean up the text to get just the trainer name
                clean_name = clean_trainer_name(text)
                if clean_name:
                    return clean_name
        
        # Look for text that might be trainer names
        text = element.get_text(strip=True)
        if text and len(text) > 1 and not text.isdigit():
            clean_name = clean_trainer_name(text)
            if clean_name:
                return clean_name
        
        return None
        
    except Exception as e:
        print(f"Error extracting trainer name: {e}")
        return None

def clean_trainer_name(text):
    """
    Clean up trainer name by extracting just the name part
    """
    try:
        # Remove common suffixes and prefixes
        text = re.sub(r'\(.*?\)', '', text)  # Remove parentheses content
        text = re.sub(r'Badge.*', '', text)  # Remove badge info
        text = re.sub(r'type.*', '', text)   # Remove type info
        text = re.sub(r'#\d+.*', '', text)  # Remove Pokemon numbers
        text = re.sub(r'Level \d+.*', '', text)  # Remove level info
        
        # Clean up whitespace
        text = text.strip()
        
        # Return only if it's a reasonable length and doesn't contain numbers
        if 2 <= len(text) <= 20 and not re.search(r'\d', text):
            return text
        
        return None
        
    except Exception as e:
        print(f"Error cleaning trainer name: {e}")
        return None

def extract_pokemon_from_element(element):
    """
    Extract Pokemon data from an element
    """
    pokemon_list = []
    
    try:
        # Look for Pokemon links
        pokemon_links = element.find_all('a', href=re.compile(r'pokemon', re.I))
        
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                # Try to find level in the same element
                level = extract_level_from_text(element.get_text())
                
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",  # Would need Pokemon ID lookup
                    "level": level
                }
                pokemon_list.append(pokemon_data)
        
        # Also look for Pokemon mentioned in text without links
        text = element.get_text()
        pokemon_names = extract_pokemon_names_from_text(text)
        for pokemon_name in pokemon_names:
            level = extract_level_from_text(text)
            pokemon_data = {
                "name": pokemon_name,
                "id": "",
                "level": level
            }
            pokemon_list.append(pokemon_data)
        
        return pokemon_list
        
    except Exception as e:
        print(f"Error extracting Pokemon from element: {e}")
        return []

def extract_pokemon_names_from_text(text):
    """
    Extract Pokemon names from text content
    """
    pokemon_names = []
    
    try:
        # Look for Pokemon names that are mentioned in the text
        # This is a simple approach - could be improved with a Pokemon name database
        pokemon_patterns = [
            r'Lillipup', r'Pansage', r'Pansear', r'Panpour', r'Herdier', r'Watchog',
            r'Whirlipede', r'Dwebble', r'Leavanny', r'Emolga', r'Zebstrika',
            r'Krokorok', r'Palpitoad', r'Excadrill', r'Swoobat', r'Unfezant', r'Swanna',
            r'Vanillish', r'Cryogonal', r'Beartic', r'Fraxure', r'Druddigon', r'Haxorus',
            r'Cofagrigus', r'Jellicent', r'Golurk', r'Chandelure', r'Scrafty', r'Liepard',
            r'Krookodile', r'Bisharp', r'Reuniclus', r'Musharna', r'Sigilyph', r'Gothitelle',
            r'Throh', r'Sawk', r'Conkeldurr', r'Mienshao', r'Accelgor', r'Bouffalant',
            r'Vanilluxe', r'Escavalier', r'Volcarona', r'Zekrom', r'Reshiram', r'Carracosta',
            r'Archeops', r'Zoroark', r'Klinklang', r'Seismitoad', r'Eelektross', r'Hydreigon'
        ]
        
        for pattern in pokemon_patterns:
            matches = re.findall(pattern, text, re.I)
            for match in matches:
                if match not in pokemon_names:
                    pokemon_names.append(match)
        
        return pokemon_names
        
    except Exception as e:
        print(f"Error extracting Pokemon names from text: {e}")
        return []

def extract_badge_from_element(element):
    """
    Extract badge information from an element
    """
    try:
        # Look for badge information
        badge_text = element.get_text()
        badge_match = re.search(r'(\w+)\s+Badge', badge_text, re.I)
        if badge_match:
            badge_name = badge_match.group(1) + " Badge"
            return {"name": badge_name, "type": ""}
        
        return {"name": "", "type": ""}
        
    except Exception as e:
        print(f"Error extracting badge: {e}")
        return {"name": "", "type": ""}

def parse_bulbapedia_table(table):
    """
    Parse trainer information from Bulbapedia table structure
    """
    trainers = []
    
    try:
        # Look for gym leader information in the table
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
                
            # Check if this row contains gym leader information
            text_content = ' '.join([cell.get_text(strip=True) for cell in cells])
            
            # Look for gym leader patterns
            if any(keyword in text_content.lower() for keyword in ['gym', 'leader', 'roxie', 'badge']):
                trainer_data = parse_bulbapedia_row(row)
                if trainer_data:
                    trainers.append(trainer_data)
        
        return trainers
        
    except Exception as e:
        print(f"Error parsing Bulbapedia table: {e}")
        return []

def parse_gym_leaders(soup):
    """
    Parse gym leader information from the page
    """
    trainers = []
    
    try:
        # Look for Roxie specifically (gym leader)
        roxie_sections = soup.find_all(string=re.compile(r'Roxie', re.I))
        
        for section in roxie_sections:
            parent = section.parent
            while parent and parent.name != 'body':
                # Look for trainer data in the parent structure
                trainer_data = extract_trainer_from_section(parent)
                if trainer_data:
                    trainers.append(trainer_data)
                    break
                parent = parent.parent
        
        return trainers
        
    except Exception as e:
        print(f"Error parsing gym leaders: {e}")
        return []

def parse_bulbapedia_row(row):
    """
    Parse trainer information from a Bulbapedia table row
    """
    try:
        trainer_data = {
            "location": "",
            "trainer name": "",
            "trainer.png": "",
            "badge name": "",
            "badge type": "",
            "pokemon": []
        }
        
        # Look for trainer name
        bold_elements = row.find_all(['b', 'strong', 'big'])
        for bold in bold_elements:
            text = bold.get_text(strip=True)
            if text and len(text) > 1 and not text.isdigit():
                trainer_data["trainer name"] = text
                break
        
        # Look for images (trainer sprite)
        img = row.find('img')
        if img and img.get('src'):
            trainer_data["trainer.png"] = img['src']
        
        # Look for Pokemon information in the row
        pokemon_links = row.find_all('a', href=re.compile(r'pokemon|pokémon', re.I))
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                # Try to extract level from surrounding text
                level = extract_level_from_text(link.parent.get_text())
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",  # Would need Pokemon ID lookup
                    "level": level
                }
                trainer_data["pokemon"].append(pokemon_data)
        
        # Look for badge information
        badge_links = row.find_all('a', href=re.compile(r'badge', re.I))
        for link in badge_links:
            badge_name = link.get_text(strip=True)
            if badge_name:
                trainer_data["badge name"] = badge_name
                break
        
        # Only return if we found some useful data
        if trainer_data["trainer name"] or trainer_data["pokemon"]:
            return trainer_data
            
    except Exception as e:
        print(f"Error parsing Bulbapedia row: {e}")
    
    return None

def extract_trainer_from_section(section):
    """
    Extract trainer information from a section element
    """
    try:
        trainer_data = {
            "location": "",
            "trainer name": "",
            "trainer.png": "",
            "badge name": "",
            "badge type": "",
            "pokemon": []
        }
        
        # Look for trainer name in the section
        bold_elements = section.find_all(['b', 'strong', 'big'])
        for bold in bold_elements:
            text = bold.get_text(strip=True)
            if text and len(text) > 1 and 'Roxie' in text:
                trainer_data["trainer name"] = text
                break
        
        # Look for images
        img = section.find('img')
        if img and img.get('src'):
            trainer_data["trainer.png"] = img['src']
        
        # Look for Pokemon information
        pokemon_links = section.find_all('a', href=re.compile(r'pokemon|pokémon', re.I))
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                level = extract_level_from_text(link.parent.get_text())
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",
                    "level": level
                }
                trainer_data["pokemon"].append(pokemon_data)
        
        # Look for badge information
        badge_links = section.find_all('a', href=re.compile(r'badge', re.I))
        for link in badge_links:
            badge_name = link.get_text(strip=True)
            if badge_name:
                trainer_data["badge name"] = badge_name
                break
        
        # Only return if we found some useful data
        if trainer_data["trainer name"] or trainer_data["pokemon"]:
            return trainer_data
            
    except Exception as e:
        print(f"Error extracting trainer from section: {e}")
    
    return None

def parse_trainer_row(row):
    """
    Parse trainer information from a table row
    """
    try:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
            
        trainer_data = {
            "location": "",
            "trainer name": "",
            "trainer.png": "",
            "badge name": "",
            "badge type": "",
            "pokemon": []
        }
        
        # Extract text from all cells
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        # Look for trainer name (usually in bold or first cell)
        for cell in cells:
            bold_text = cell.find('b')
            if bold_text:
                trainer_data["trainer name"] = bold_text.get_text(strip=True)
                break
        
        # Look for images (trainer sprite)
        img = row.find('img')
        if img and img.get('src'):
            trainer_data["trainer.png"] = img['src']
        
        # Look for Pokemon information
        pokemon_links = row.find_all('a', href=re.compile(r'pokemon|pokémon', re.I))
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                # Try to extract level if present
                level = extract_level_from_text(link.parent.get_text())
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",  # Would need Pokemon ID lookup
                    "level": level
                }
                trainer_data["pokemon"].append(pokemon_data)
        
        # Only return if we found some useful data
        if trainer_data["trainer name"] or trainer_data["pokemon"]:
            return trainer_data
            
    except Exception as e:
        print(f"Error parsing trainer row: {e}")
    
    return None

def parse_trainer_div(div):
    """
    Parse trainer information from a div element
    """
    try:
        trainer_data = {
            "location": "",
            "trainer name": "",
            "trainer.png": "",
            "badge name": "",
            "badge type": "",
            "pokemon": []
        }
        
        # Look for trainer name
        bold_elements = div.find_all(['b', 'strong'])
        for bold in bold_elements:
            text = bold.get_text(strip=True)
            if text and len(text) > 1:
                trainer_data["trainer name"] = text
                break
        
        # Look for images
        img = div.find('img')
        if img and img.get('src'):
            trainer_data["trainer.png"] = img['src']
        
        # Look for Pokemon links
        pokemon_links = div.find_all('a', href=re.compile(r'pokemon|pokémon', re.I))
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                level = extract_level_from_text(link.parent.get_text())
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",
                    "level": level
                }
                trainer_data["pokemon"].append(pokemon_data)
        
        # Only return if we found some useful data
        if trainer_data["trainer name"] or trainer_data["pokemon"]:
            return trainer_data
            
    except Exception as e:
        print(f"Error parsing trainer div: {e}")
    
    return None

def extract_level_from_text(text):
    """
    Extract Pokemon level from text using regex
    """
    level_match = re.search(r'Lv\.?\s*(\d+)', text, re.I)
    if level_match:
        return int(level_match.group(1))
    return ""

def save_to_json(data, filename="trainers.json"):
    """
    Save trainer data to JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def parse_debug_html():
    """
    Parse the debug_html.html file directly to extract trainer data
    """
    try:
        with open('../../debug_html.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        trainers_data = []
        
        # Look for Roxie (gym leader) specifically
        roxie_data = extract_roxie_data(soup)
        if roxie_data:
            trainers_data.append(roxie_data)
        
        # Look for other trainers in the HTML
        other_trainers = extract_other_trainers(soup)
        trainers_data.extend(other_trainers)
        
        # Clean up and remove duplicates
        cleaned_data = clean_trainer_data(trainers_data)
        
        return cleaned_data
        
    except Exception as e:
        print(f"Error parsing debug HTML: {e}")
        return []

def clean_trainer_data(trainers_data):
    """
    Clean up trainer data by removing duplicates and invalid entries
    """
    cleaned = []
    seen_names = set()
    
    for trainer in trainers_data:
        # Skip if trainer name is empty or too generic
        if not trainer.get("trainer name") or len(trainer.get("trainer name", "")) < 2:
            continue
            
        # Skip if it's a duplicate
        trainer_name = trainer.get("trainer name", "").strip()
        if trainer_name in seen_names:
            continue
            
        # Skip if Pokemon list contains invalid entries
        if trainer.get("pokemon"):
            valid_pokemon = []
            for pokemon in trainer["pokemon"]:
                pokemon_name = pokemon.get("name", "").strip()
                # Skip if Pokemon name is empty, too long, or contains URLs
                if (pokemon_name and 
                    len(pokemon_name) < 50 and 
                    not pokemon_name.startswith("http") and
                    not pokemon_name.startswith("https")):
                    valid_pokemon.append(pokemon)
            trainer["pokemon"] = valid_pokemon
        
        # Only add if we have meaningful data
        if (trainer_name and 
            (trainer.get("pokemon") or 
             trainer.get("trainer.png") or 
             trainer.get("badge name"))):
            cleaned.append(trainer)
            seen_names.add(trainer_name)
    
    return cleaned

def extract_roxie_data(soup):
    """
    Extract Roxie's data specifically
    """
    try:
        trainer_data = {
            "location": "Virbank City",
            "trainer name": "Roxie",
            "trainer.png": "",
            "badge name": "Toxic Badge",
            "badge type": "Poison",
            "pokemon": []
        }
        
        # Find Roxie's image
        roxie_img = soup.find('img', alt=re.compile(r'Roxie', re.I))
        if roxie_img and roxie_img.get('src'):
            trainer_data["trainer.png"] = roxie_img['src']
        
        # Look for Pokemon in tables that contain Roxie's data
        tables = soup.find_all('table')
        for table in tables:
            # Check if this table contains Roxie's Pokemon
            table_text = table.get_text()
            if 'Roxie' in table_text and any(pokemon in table_text for pokemon in ['Koffing', 'Whirlipede', 'Venipede']):
                pokemon_data = extract_pokemon_from_table(table)
                trainer_data["pokemon"].extend(pokemon_data)
        
        # If no Pokemon found in tables, look for specific Pokemon patterns
        if not trainer_data["pokemon"]:
            pokemon_data = extract_roxie_pokemon_directly(soup)
            trainer_data["pokemon"] = pokemon_data
        
        return trainer_data
        
    except Exception as e:
        print(f"Error extracting Roxie data: {e}")
        return None

def extract_roxie_pokemon_directly(soup):
    """
    Extract Roxie's Pokemon data directly from the HTML
    """
    pokemon_list = []
    
    try:
        # Look for specific Pokemon mentioned in the text
        pokemon_names = ['Koffing', 'Whirlipede', 'Venipede']
        
        for pokemon_name in pokemon_names:
            # Find all mentions of this Pokemon
            pokemon_links = soup.find_all('a', href=re.compile(pokemon_name, re.I))
            
            for link in pokemon_links:
                # Get the parent element to find level information
                parent = link.parent
                level = extract_level_from_text(parent.get_text())
                
                # Only add if we found a valid level or if it's clearly a Pokemon
                if level or pokemon_name.lower() in link.get_text().lower():
                    pokemon_data = {
                        "name": pokemon_name,
                        "id": "",  # Would need Pokemon ID lookup
                        "level": level
                    }
                    pokemon_list.append(pokemon_data)
                    break  # Only add each Pokemon once
        
        return pokemon_list
        
    except Exception as e:
        print(f"Error extracting Roxie Pokemon directly: {e}")
        return []

def extract_pokemon_from_table(table):
    """
    Extract Pokemon data from a table
    """
    pokemon_list = []
    
    try:
        # Look for Pokemon links in the table
        pokemon_links = table.find_all('a', href=re.compile(r'pokemon|pokémon', re.I))
        
        for link in pokemon_links:
            pokemon_name = link.get_text(strip=True)
            if pokemon_name and len(pokemon_name) > 1:
                # Try to find the level in the same row or nearby
                level = extract_level_from_text(link.parent.get_text())
                
                pokemon_data = {
                    "name": pokemon_name,
                    "id": "",  # Would need Pokemon ID lookup
                    "level": level
                }
                pokemon_list.append(pokemon_data)
        
        return pokemon_list
        
    except Exception as e:
        print(f"Error extracting Pokemon from table: {e}")
        return []

def extract_other_trainers(soup):
    """
    Extract other trainer data from the HTML
    """
    trainers = []
    
    try:
        # Look for other trainer classes mentioned in the HTML
        trainer_classes = ['Youngster', 'Worker', 'Lass', 'Roughneck', 'Guitarist']
        
        for trainer_class in trainer_classes:
            # Find sections with this trainer class
            sections = soup.find_all(string=re.compile(trainer_class, re.I))
            
            for section in sections:
                parent = section.parent
                while parent and parent.name != 'body':
                    trainer_data = extract_trainer_from_section(parent)
                    if trainer_data:
                        trainers.append(trainer_data)
                        break
                    parent = parent.parent
        
        return trainers
        
    except Exception as e:
        print(f"Error extracting other trainers: {e}")
        return []

if __name__ == "__main__":
    url = "https://pokemondb.net/black-white/gymleaders-elitefour#gym-1"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    print(f"Scraping data from: {url}")
    trainers_data = scrape_trainers(url)
    
    if trainers_data:
        print(f"Found {len(trainers_data)} trainers")
        save_to_json(trainers_data)
        
        # Print first trainer as example
        if trainers_data:
            print("\nFirst trainer data:")
            print(json.dumps(trainers_data[0], indent=2))
    else:
        print("No trainer data found. The HTML structure might be different than expected.")
        print("You may need to inspect the HTML manually to find the correct selectors.")
