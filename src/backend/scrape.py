import requests
from bs4 import BeautifulSoup
import re

def _extract_location_from_context(context_text):
    """Extract location from context text around a trainers section"""
    # Look for location patterns in the context
    location_patterns = [
        # Numbered sections like "1 Route 20" or "2.1 Aspertia City"
        r'^\d+(?:\.\d+)?\s*([A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))',
        # Simple location names on their own line
        r'^([A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))$',
        # Location names at the start of a line
        r'^([A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))',
    ]
    
    # Split into lines and look for location patterns
    lines = context_text.split('\n')
    for line in reversed(lines):  # Look from bottom up (most recent first)
        line = line.strip()
        
        # Skip lines that are too long (likely not section headers)
        if len(line) > 100:
            continue
            
        # Skip lines that contain trainer-related text (likely not location headers)
        if any(word in line.lower() for word in ['trainer', 'pokemon', 'reward', 'lv.', 'item']):
            continue
            
        for pattern in location_patterns:
            match = re.search(pattern, line, re.MULTILINE)
            if match:
                location = match.group(1).strip()
                # Clean up the location name
                location = re.sub(r'^\d+(?:\.\d+)?\s*', '', location)  # Remove leading numbers
                location = location.split('\n')[0]  # Take first line if multiline
                location = location.split(' ')[0] if len(location.split(' ')) > 3 else location  # Take first few words if too long
                
                # Validate the location name
                if (len(location) > 2 and len(location) < 30 and 
                    not any(word in location.lower() for word in ['trainer', 'pokemon', 'reward', 'item', 'level', 'type', 'ability'])):
                    return location
    
    return "Unknown Location"

def _build_section_location_map(soup):
    """Build a map of text positions to section locations by analyzing HTML structure"""
    section_locations = []
    text_content = soup.get_text()
    
    # Find all heading elements (h1, h2, h3, h4, h5, h6)
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        heading_text = heading.get_text().strip()
        
        # Look for location patterns in headings
        location_patterns = [
            r'^\d+(?:\.\d+)?\s*([A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))',
            r'^([A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, heading_text)
            if match:
                location = match.group(1).strip()
                # Clean up the location name
                location = re.sub(r'^\d+(?:\.\d+)?\s*', '', location)
                location = location.split('\n')[0]
                
                if (len(location) > 2 and len(location) < 50 and
                    not any(word in location.lower() for word in ['trainer', 'pokemon', 'reward', 'item', 'level', 'type', 'ability'])):
                    
                    # Find the position of this heading in the text
                    pos = text_content.find(heading_text)
                    if pos != -1:
                        section_locations.append({
                            'position': pos,
                            'location': location,
                            'heading_level': heading.name
                        })
                    break
    
    # Also look for location patterns in the text content directly
    # This catches locations that might not be in headings
    location_patterns = [
        r'\n(\d+(?:\.\d+)?\s*[A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))\n',
        r'\n([A-Z][A-Za-z\s]+(?:City|Town|Gym|Route|Cave|Forest|Mountain|Beach|Island|Complex|Building|House|Area|Zone|Place|Spot))\n',
    ]
    
    for pattern in location_patterns:
        for match in re.finditer(pattern, text_content):
            location = match.group(1).strip()
            # Clean up the location name
            location = re.sub(r'^\d+(?:\.\d+)?\s*', '', location)
            location = location.split('\n')[0]
            
            if (len(location) > 2 and len(location) < 50 and
                not any(word in location.lower() for word in ['trainer', 'pokemon', 'reward', 'item', 'level', 'type', 'ability'])):
                
                section_locations.append({
                    'position': match.start(),
                    'location': location,
                    'heading_level': 'text'
                })
    
    # Sort by position
    section_locations.sort(key=lambda x: x['position'])
    
    return section_locations

def _find_trainer_location(trainer_position, section_locations, text_content):
    """Find the most recent section location before a trainer position"""
    # Find the most recent section before the trainer
    current_location = "Unknown Location"
    
    for section in reversed(section_locations):
        if section['position'] < trainer_position:
            # Additional validation: check if this section is close enough to the trainer
            # and if there are any "Trainers" sections between this location and the trainer
            text_between = text_content[section['position']:trainer_position]
            
            # If there's a "Trainers" section between the location and trainer, it's likely the right location
            if "Trainers" in text_between:
                current_location = section['location']
                break
            # If no "Trainers" section but this is the closest location, use it
            elif current_location == "Unknown Location":
                current_location = section['location']
    
    return current_location

def scrape_page_content(url):
    """Scrape a webpage and return content with font size information"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get page title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract content with font size information
        content_with_styles = []
        
        # Find all elements that contain text
        for element in soup.find_all(text=True):
            if element.strip():  # Only process non-empty text nodes
                parent = element.parent
                if parent:
                    # Get font size from various sources
                    font_size = None
                    
                    # Check inline style
                    if parent.get('style'):
                        style_match = re.search(r'font-size:\s*([^;]+)', parent.get('style'))
                        if style_match:
                            font_size = style_match.group(1).strip()
                    
                    # Check class-based font sizes (common in Bulbapedia)
                    if parent.get('class'):
                        classes = parent.get('class')
                        for cls in classes:
                            if 'font-size' in cls or any(size in cls for size in ['large', 'medium', 'small', 'tiny']):
                                font_size = cls
                    
                    # Check if it's a heading (h1, h2, etc.) - these typically have larger fonts
                    if parent.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        font_size = f"heading-{parent.name}"
                    
                    content_with_styles.append({
                        'text': element.strip(),
                        'font_size': font_size or 'default',
                        'tag': parent.name if parent else 'unknown'
                    })
        
        # Also get plain text for comparison
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        plain_lines = [line for line in text.split('\n') if line.strip()]
        
        return {
            'title': title,
            'url': url,
            'total_lines': len(plain_lines),
            'ordered_content': plain_lines,
            'content_with_styles': content_with_styles
        }
        
    except requests.RequestException as e:
        return {'error': f"Request failed: {e}"}
    except Exception as e:
        return {'error': f"Scraping failed: {e}"}

def print_ordered_content(data):
    """Print the scraped content in original page order (top to bottom)"""
    if 'error' in data:
        print(f"Error: {data['error']}")
        return
    
    print("=" * 80)
    print(f"PAGE TITLE: {data['title']}")
    print(f"URL: {data['url']}")
    print(f"TOTAL LINES: {data['total_lines']}")
    print("=" * 80)
    print("\nPAGE CONTENT (Top to Bottom):")
    print("-" * 80)
    
    for i, line in enumerate(data['ordered_content'], 1):
        print(f"{i:4d}: {line}")
    
    print("-" * 80)
    print(f"Total lines processed: {len(data['ordered_content'])}")

def print_content_with_font_sizes(data):
    """Print the scraped content with font size information"""
    if 'error' in data:
        print(f"Error: {data['error']}")
        return
    
    print("=" * 80)
    print(f"PAGE TITLE: {data['title']}")
    print(f"URL: {data['url']}")
    print(f"TOTAL TEXT ELEMENTS: {len(data['content_with_styles'])}")
    print("=" * 80)
    print("\nCONTENT WITH FONT SIZES (Top to Bottom):")
    print("-" * 80)
    
    for i, item in enumerate(data['content_with_styles'], 1):
        font_info = f"[{item['font_size']}]" if item['font_size'] != 'default' else "[default]"
        tag_info = f"<{item['tag']}>" if item['tag'] != 'unknown' else ""
        print(f"{i:4d}: {font_info} {tag_info} {item['text']}")
    
    print("-" * 80)
    print(f"Total text elements processed: {len(data['content_with_styles'])}")

def scrape_full_html(url):
    """Scrape a webpage and return the complete HTML content"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get page title
        title = soup.title.string if soup.title else "No title found"
        
        # Return the complete HTML as a string
        html_content = soup.prettify()
        
        return {
            'title': title,
            'url': url,
            'html_content': html_content,
            'total_lines': len(html_content.split('\n'))
        }
        
    except requests.RequestException as e:
        return {'error': f"Request failed: {e}"}
    except Exception as e:
        return {'error': f"Scraping failed: {e}"}

def print_full_html(data):
    """Print the complete HTML content from top to bottom"""
    if 'error' in data:
        print(f"Error: {data['error']}")
        return
    
    print("=" * 80)
    print(f"PAGE TITLE: {data['title']}")
    print(f"URL: {data['url']}")
    print(f"TOTAL HTML LINES: {data['total_lines']}")
    print("=" * 80)
    print("\nCOMPLETE HTML CONTENT (Top to Bottom):")
    print("-" * 80)
    
    # Split HTML into lines and print with line numbers
    html_lines = data['html_content'].split('\n')
    for i, line in enumerate(html_lines, 1):
        print(f"{i:6d}: {line}")
    
    print("-" * 80)
    print(f"Total HTML lines: {len(html_lines)}")

def extract_trainer_names(url):
    """Extract all trainer names and locations from a Bulbapedia walkthrough page in order of appearance"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get page title
        title = soup.title.string if soup.title else "No title found"
        
        # First, build a map of sections and their locations by analyzing HTML structure
        section_locations = _build_section_location_map(soup)
        
        # Find all trainer entries using Bulbapedia's trainer template structure
        trainer_data = []
        
        # Get all text content and search for trainer patterns
        text_content = soup.get_text()
        
        # More specific patterns based on the actual output we saw
        trainer_patterns = [
            # Pattern 1: "Class Name" followed by reward
            r'(Youngster\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Lass\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(School Kid\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Leader\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Hiker\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Janitor\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(PKMN Trainer\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Trainer\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Twins\s+[A-Za-z\s&]+)\s+Reward:\s*\$[\d,]+',
            r'(Nursery Aide\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Preschooler\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Pokémon Ranger\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+',
            r'(Team Plasma Grunt)\s+Reward:\s*\$[\d,]+',
            
            # Pattern 2: Special cases with additional text
            r'(Pokémon Ranger\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+Autumn only',
            r'(Pokémon Ranger\s+[A-Za-z]+)\s+Reward:\s*\$[\d,]+Requires',
        ]
        
        # Find all matches with their positions to preserve order
        for pattern in trainer_patterns:
            for match in re.finditer(pattern, text_content):
                trainer_name = match.group(1).strip()
                
                # Find the location using the section map
                location = _find_trainer_location(match.start(), section_locations, text_content)
                
                # Check if this trainer is already in our list
                trainer_exists = any(data['name'] == trainer_name for data in trainer_data)
                
                if not trainer_exists:
                    trainer_data.append({
                        'name': trainer_name,
                        'location': location,
                        'position': match.start()
                    })
        
        # Sort by position to maintain document order
        trainer_data.sort(key=lambda x: x['position'])
        
        # Extract just the names for backward compatibility
        trainer_names = [data['name'] for data in trainer_data]
        
        return {
            'title': title,
            'url': url,
            'trainer_names': trainer_names,
            'trainer_data': trainer_data,  # Full data with locations
            'total_trainers': len(trainer_names)
        }
        
    except requests.RequestException as e:
        return {'error': f"Request failed: {e}"}
    except Exception as e:
        return {'error': f"Scraping failed: {e}"}

def print_trainer_names(data):
    """Print all extracted trainer names with their locations"""
    if 'error' in data:
        print(f"Error: {data['error']}")
        return
    
    print("=" * 80)
    print(f"PAGE TITLE: {data['title']}")
    print(f"URL: {data['url']}")
    print(f"TOTAL TRAINERS FOUND: {data['total_trainers']}")
    print("=" * 80)
    print("\nTRAINER NAMES WITH LOCATIONS (Top to Bottom Order):")
    print("-" * 80)
    
    # Use trainer_data if available, otherwise fall back to trainer_names
    if 'trainer_data' in data:
        for i, trainer_info in enumerate(data['trainer_data'], 1):
            print(f"{i:3d}: {trainer_info['name']} - {trainer_info['location']}")
    else:
        for i, trainer_name in enumerate(data['trainer_names'], 1):
            print(f"{i:3d}: {trainer_name}")
    
    print("-" * 80)
    print(f"Total trainers found: {len(data['trainer_names'])}")

# Example usage
if __name__ == "__main__":
    # Default URL
    url = "https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Black_2_and_White_2/Part_3"
    
    # You can change the URL here or pass it as a parameter
    # url = "https://example.com"  # Replace with your desired URL
    
    print("Scraping webpage...")
    
    # Get content with font information
    data = scrape_page_content(url)
    
    # Get complete HTML content
    html_data = scrape_full_html(url)
    
    # Extract trainer names
    trainer_data = extract_trainer_names(url)
    
    # Print trainer names first
    print("\n" + "="*80)
    print("OPTION 1: Trainer Names Extraction")
    print("="*80)
    print_trainer_names(trainer_data)




