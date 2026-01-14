import re
import json
import aiohttp
from bs4 import BeautifulSoup
from plugins.utils import fetch_url
from config import USER_AGENT

class WatchAnimeWorldScraper:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def scrape_episode(self, url):
        """Main scraping function"""
        try:
            # Step 1: Fetch episode page
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Step 2: Find iframe
            iframe = soup.find('iframe', {'id': 'video-iframe'})
            if not iframe:
                return {"error": "Video iframe not found"}
            
            iframe_url = iframe.get('src')
            if not iframe_url.startswith('http'):
                iframe_url = f"https:{iframe_url}" if iframe_url.startswith('//') else f"https://watchanimeworld.net{iframe_url}"
            
            # Step 3: Extract player configuration
            player_data = await self.extract_player_config(iframe_url)
            if "error" in player_data:
                return player_data
            
            # Step 4: Extract episode info
            episode_info = self.extract_episode_info(soup)
            
            return {
                "success": True,
                "episode_info": episode_info,
                "player_data": player_data,
                "source_url": iframe_url
            }
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    async def extract_player_config(self, iframe_url):
        """Extract player configuration from iframe"""
        try:
            headers = {
                'Referer': 'https://watchanimeworld.net/',
                'User-Agent': USER_AGENT
            }
            
            html = await fetch_url(self.session, iframe_url, headers)
            if not html:
                return {"error": "Failed to fetch iframe"}
            
            # Look for player configuration in script tags
            soup = BeautifulSoup(html, 'lxml')
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string:
                    # Look for m3u8 URLs
                    m3u8_match = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\']*)', script.string, re.IGNORECASE)
                    if m3u8_match:
                        m3u8_url = m3u8_match.group(0)
                        return {
                            "type": "m3u8",
                            "url": m3u8_url,
                            "referer": iframe_url
                        }
                    
                    # Look for mp4 URLs
                    mp4_match = re.search(r'(https?://[^\s"\'<>]+\.mp4[^\s"\']*)', script.string, re.IGNORECASE)
                    if mp4_match:
                        mp4_url = mp4_match.group(0)
                        return {
                            "type": "mp4",
                            "url": mp4_url,
                            "referer": iframe_url
                        }
            
            # Try to find video source in video tags
            video_tag = soup.find('video')
            if video_tag:
                source = video_tag.find('source')
                if source and source.get('src'):
                    src = source.get('src')
                    if src.endswith('.m3u8'):
                        return {
                            "type": "m3u8",
                            "url": src,
                            "referer": iframe_url
                        }
                    elif src.endswith('.mp4'):
                        return {
                            "type": "mp4",
                            "url": src,
                            "referer": iframe_url
                        }
            
            return {"error": "No video source found"}
            
        except Exception as e:
            return {"error": f"Failed to extract player config: {str(e)}"}
    
    def extract_episode_info(self, soup):
        """Extract episode title and information"""
        try:
            title_tag = soup.find('h1', {'class': 'entry-title'})
            title = title_tag.text.strip() if title_tag else "Unknown Episode"
            
            # Clean title
            title = re.sub(r'\s+', ' ', title)
            
            return {
                "title": title,
                "cleaned_title": self.clean_filename(title)
            }
        except:
            return {
                "title": "Episode",
                "cleaned_title": "episode"
            }
    
    def clean_filename(self, text):
        """Clean text for filename"""
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Trim
        return text.strip()
