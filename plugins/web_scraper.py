import aiohttp
import feedparser
from typing import List, Dict, Optional
from config import config
from loguru import logger
import asyncio
import hashlib

class WebScraper:
    def __init__(self):
        self.rss_url = config.RSS_URL
        self.session = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def get_latest_anime(self, last_hash: Optional[str] = None, limit: int = 30) -> Optional[Dict]:
        """
        Get latest anime from RSS feed asynchronously
        
        Args:
            last_hash: Last processed hash
            limit: Maximum items to fetch
            
        Returns:
            Dict with anime array and latest hash
        """
        try:
            await self.init_session()
            
            async with self.session.get(self.rss_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch RSS: {response.status}")
                    return None
                
                content = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if not feed.entries:
                logger.warning("No entries in RSS feed")
                return None
            
            anime_dict = {}
            latest_hash = None
            
            for i, entry in enumerate(feed.entries[:limit]):
                entry_id = entry.get('id', '')
                
                # Stop if we reached last processed hash
                if last_hash and entry_id == last_hash:
                    break
                
                # Extract info from entry
                title = entry.get('title', '')
                magnet = entry.get('link', '')
                categories = entry.get('tags', [{}])
                
                # Parse categories for quality and name
                anime_name = ""
                quality = "Unknown"
                
                for cat in categories:
                    cat_term = cat.get('term', '')
                    if '-' in cat_term:
                        parts = cat_term.split('-')
                        anime_name = parts[0].strip()
                        if len(parts) > 1:
                            quality = parts[-1].strip()
                        break
                
                if not anime_name:
                    # Fallback: try to extract from title
                    if ']' in title and '-' in title:
                        parts = title.split(']')
                        if len(parts) > 1:
                            anime_name = parts[1].split('-')[0].strip()
                
                # Create unique hash for this entry
                entry_hash = hashlib.md5(f"{title}{magnet}".encode()).hexdigest()
                
                if i == 0:
                    latest_hash = entry_id
                
                # Group by anime name
                if anime_name in anime_dict:
                    anime_dict[anime_name]['magnets'].append(magnet)
                    anime_dict[anime_name]['hashes'].append(entry_hash)
                    anime_dict[anime_name]['qualities'].append(quality)
                    anime_dict[anime_name]['titles'].append(title)
                else:
                    anime_dict[anime_name] = {
                        'name': anime_name,
                        'magnets': [magnet],
                        'hashes': [entry_hash],
                        'qualities': [quality],
                        'titles': [title]
                    }
            
            # Convert dict to array
            anime_array = list(anime_dict.values())
            
            if not anime_array:
                return None
            
            return {
                'array': anime_array,
                'hash': latest_hash
            }
            
        except Exception as e:
            logger.error(f"Error fetching anime: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Test RSS feed connection"""
        try:
            await self.init_session()
            async with self.session.get(self.rss_url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"RSS connection test failed: {e}")
            return False
