import requests
from bs4 import BeautifulSoup

url = "https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Black_2_and_White_2/Part_2"
response = requests.get(url)

#print(response.text)

soup = BeautifulSoup(response.text, "html.parser")

print("Page Title:", soup.title.string)

for link in soup.find_all("a", href=True):
    print("Link:", link['href'])

