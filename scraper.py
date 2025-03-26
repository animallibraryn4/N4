import requests
from bs4 import BeautifulSoup
from config import Config
from typing import Dict, List, Optional

class AnimeWorldScraper:
    @staticmethod
    def search_anime(query: str) -> List[Dict]:
        """Search anime on anime-world.co"""
        try:
            url = f"{Config.SEARCH_URL}?s={query.replace(' ', '+')}"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for item in soup.select('div.post-item'):
                title = item.select_one('h2 a').text.strip()
                link = item.select_one('h2 a')['href']
                image = item.select_one('img')['src']
                
                results.append({
                    'title': title,
                    'link': link,
                    'image': image
                })
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    @staticmethod
    def get_anime_details(url: str) -> Dict:
        """Get detailed information about an anime"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {
                'title': soup.select_one('h1.entry-title').text.strip(),
                'description': soup.select_one('div.entry-content p').text.strip(),
                'episodes': [],
                'download_links': {}
            }
            
            # Extract episodes and download links (adjust selectors as needed)
            for episode in soup.select('div.episode-list a'):
                ep_num = episode.text.strip().split()[-1]
                ep_link = episode['href']
                details['episodes'].append({
                    'number': ep_num,
                    'link': ep_link
                })
            
            # Extract download links (example - adjust based on actual site structure)
            for quality in soup.select('div.download-links a'):
                qual = quality.text.strip()
                link = quality['href']
                details['download_links'][qual] = link
            
            return details
        except Exception as e:
            print(f"Details error: {e}")
            return {}
