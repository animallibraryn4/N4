# torrents.py
import requests
from bs4 import BeautifulSoup

def search_dual_audio_anime(query):
    url = f"https://nyaa.si/?q={query}+dual+audio&f=0&c=1_2"  # 1_2 = Anime category
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    torrents = []
    for row in soup.select('table.torrent-list tbody tr'):
        name = row.select_one('td[colspan="2"] a').text
        magnet = row.select_one('a[href^="magnet:"]')['href']
        size = row.select('td.text-center')[1].text
        seeders = int(row.select('td.text-center')[3].text)
        
        if "dual audio" in name.lower() and seeders > 10:  # Filter active torrents
            torrents.append({
                "name": name,
                "magnet": magnet,
                "size": size,
                "seeders": seeders
            })
    
    return torrents
