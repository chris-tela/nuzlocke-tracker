import requests
from bs4 import BeautifulSoup
import re

def scrape_and_sort_page(url):
    """Scrape a webpage and return sorted content"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get page title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract all text content
        text_content = soup.get_text()
        
        # Clean up the text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Split into lines and filter out empty lines
        lines = [line for line in text.split('\n') if line.strip()]
        
        # Sort lines alphabetically (case-insensitive)
        sorted_lines = sorted(lines, key=str.lower)
        
        return {
            'title': title,
            'url': url,
            'total_lines': len(lines),
            'sorted_content': sorted_lines
        }
        
    except requests.RequestException as e:
        return {'error': f"Request failed: {e}"}
    except Exception as e:
        return {'error': f"Scraping failed: {e}"}

def print_sorted_content(data):
    """Print the scraped content in a neat format"""
    if 'error' in data:
        print(f"Error: {data['error']}")
        return
    
    print("=" * 80)
    print(f"PAGE TITLE: {data['title']}")
    print(f"URL: {data['url']}")
    print(f"TOTAL LINES: {data['total_lines']}")
    print("=" * 80)
    print("\nSORTED CONTENT:")
    print("-" * 80)
    
    for i, line in enumerate(data['sorted_content'], 1):
        print(f"{i:4d}: {line}")
    
    print("-" * 80)
    print(f"Total lines processed: {len(data['sorted_content'])}")

# Example usage
if __name__ == "__main__":
    # Default URL
    url = "https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Black_2_and_White_2/Part_2"
    
    # You can change the URL here or pass it as a parameter
    # url = "https://example.com"  # Replace with your desired URL
    
    print("Scraping webpage...")
    data = scrape_and_sort_page(url)
    print_sorted_content(data)




