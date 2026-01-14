import re
import json
import aiohttp
from bs4 import BeautifulSoup
from plugins.utils import fetch_url
from config import USER_AGENT

class WatchAnimeWorldScraper:
    def __init__(self):
        self.session = None
        self.base_domain = "watchanimeworld.net"
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    # ==================== CORE FUNCTION ====================
    async def scrape_episode(self, url):
        """Meido-style scraper: Episode URL -> AJAX -> m3u8"""
        try:
            # 1️⃣ Episode page fetch (for episode_id only)
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            # 2️⃣ Extract episode_id (MOST IMPORTANT STEP)
            episode_id = self.extract_episode_id(html)
            if not episode_id:
                # Fallback: try alternate method
                episode_id = self.extract_id_from_url(url)
                if not episode_id:
                    return {"error": "Could not extract episode ID. Please check /debug"}
            
            # 3️⃣ Call WordPress AJAX endpoint (REAL SOURCE)
            ajax_response = await self.fetch_player_ajax(episode_id, url)
            if not ajax_response:
                return {"error": "AJAX request failed. Player data not found."}
            
            # 4️⃣ Extract m3u8 from AJAX response
            m3u8_url = self.extract_m3u8_from_response(ajax_response)
            if not m3u8_url:
                # Try alternative extraction methods
                m3u8_url = self.extract_from_json(ajax_response)
                if not m3u8_url:
                    return {"error": "No m3u8 found in player data. Response: " + ajax_response[:200]}
            
            # 5️⃣ Validate and fix m3u8 URL
            m3u8_url = self.fix_m3u8_url(m3u8_url)
            
            # 6️⃣ Episode info (for UI only, not for source)
            soup = BeautifulSoup(html, 'lxml')
            episode_info = self.extract_episode_info(soup)
            
            # ✅ SUCCESS: Return Meido-style response
            return {
                "success": True,
                "episode_info": episode_info,
                "player_data": {
                    "type": "m3u8",
                    "url": m3u8_url,
                    "referer": url,
                    "quality": "auto"
                },
                "source_url": url,
                "debug": {
                    "episode_id": episode_id,
                    "ajax_response_preview": ajax_response[:300] if ajax_response else "None"
                }
            }
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    # ==================== ID EXTRACTION ====================
    def extract_episode_id(self, html):
        """Extract episode/post ID from HTML (Meido's first step)"""
        patterns = [
            # WordPress post ID (most common)
            r'data-post=["\'](\d+)["\']',
            r'data-id=["\'](\d+)["\']',
            r'post["\']?\s*:\s*["\']?(\d+)',
            
            # JS variables
            r'episode_id\s*[=:]\s*["\']?(\d+)["\']?',
            r'post_id\s*[=:]\s*["\']?(\d+)["\']?',
            r'id\s*[=:]\s*["\']?(\d+)["\']?',
            r'episode["\']?\s*:\s*["\']?(\d+)',
            
            # Hidden inputs
            r'<input[^>]*name=["\']episode_id["\'][^>]*value=["\'](\d+)["\']',
            r'<input[^>]*name=["\']post_id["\'][^>]*value=["\'](\d+)["\']',
            
            # URL patterns in scripts
            r'ajax\.php\?.*?id=(\d+)',
            
            # WordPress nonce patterns (sometimes contains ID)
            r'ajax_nonce["\']?\s*:\s*["\'][^"\']*-(\d+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_id_from_url(self, url):
        """Extract ID from URL (fallback method)"""
        patterns = [
            r'episode/[^/]+-(\d+)x\d+/',  # gachiakuta-1x1/
            r'episode/(\d+)/',
            r'watch/(\d+)/',
            r'\?p=(\d+)',
            r'&id=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    # ==================== AJAX REQUEST ====================
    async def fetch_player_ajax(self, episode_id, referer_url):
        """Call WordPress admin-ajax.php (REAL SOURCE)"""
        ajax_url = f"https://{self.base_domain}/wp-admin/admin-ajax.php"
        
        # Common WordPress player actions (trying multiple)
        possible_actions = [
            "player_ajax",
            "get_player",
            "load_player",
            "episode_player",
            "anime_player",
            "watchanimeworld_player",
            "get_video",
            "load_video",
            "wp_ajax_player",
            "wp_ajax_get_player"
        ]
        
        headers = {
            "User-Agent": USER_AGENT,
            "Referer": referer_url,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": f"https://{self.base_domain}"
        }
        
        for action in possible_actions:
            try:
                data = {
                    "action": action,
                    "episode_id": episode_id,
                    "post_id": episode_id,  # Sometimes it's post_id
                    "id": episode_id,       # Sometimes just id
                }
                
                async with self.session.post(
                    ajax_url,
                    data=data,
                    headers=headers,
                    timeout=15
                ) as response:
                    
                    if response.status == 200:
                        response_text = await response.text()
                        if response_text and response_text.strip():
                            # Check if response contains video data
                            if any(keyword in response_text.lower() for keyword in ['m3u8', 'http', 'file:', 'src:', '.mp4']):
                                return response_text
                            
            except Exception as e:
                continue  # Try next action
        
        return None
    
    # ==================== M3U8 EXTRACTION ====================
    def extract_m3u8_from_response(self, response_text):
        """Extract m3u8 URL from AJAX response"""
        # Direct m3u8 URL patterns
        m3u8_patterns = [
            r'(https?://[^\s"\'\{\}<>]+\.m3u8[^\s"\'\{\}<>]*)',
            r'["\'](//[^"\']+\.m3u8[^"\']*)["\']',
            r'file\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
            r'src\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
            r'url\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
            r'video_url\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
        ]
        
        for pattern in m3u8_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                url = match if isinstance(match, str) else match[0]
                if url and '.m3u8' in url.lower():
                    return url.strip()
        
        return None
    
    def extract_from_json(self, response_text):
        """Extract m3u8 from JSON response"""
        try:
            # Try to parse as JSON
            data = json.loads(response_text)
            
            # Check common JSON structures
            if isinstance(data, dict):
                # Direct file key
                if data.get("file") and ".m3u8" in data["file"].lower():
                    return data["file"]
                
                # Sources array
                if data.get("sources") and isinstance(data["sources"], list):
                    for source in data["sources"]:
                        if source.get("file") and ".m3u8" in source["file"].lower():
                            return source["file"]
                        if source.get("src") and ".m3u8" in source["src"].lower():
                            return source["src"]
                
                # Nested data
                if data.get("data"):
                    nested = data["data"]
                    if isinstance(nested, str):
                        # Try to extract from nested string
                        m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', nested)
                        if m3u8_match:
                            return m3u8_match.group(1)
                
                # Player data
                if data.get("player_data"):
                    if isinstance(data["player_data"], str):
                        m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', data["player_data"])
                        if m3u8_match:
                            return m3u8_match.group(1)
        except json.JSONDecodeError:
            pass
        except Exception:
            pass
        
        return None
    
    def fix_m3u8_url(self, m3u8_url):
        """Fix relative or malformed m3u8 URLs"""
        if not m3u8_url:
            return m3u8_url
        
        # Fix double slashes
        m3u8_url = m3u8_url.replace('\\/', '/').replace('\\\\', '')
        
        # Add protocol if missing
        if m3u8_url.startswith('//'):
            m3u8_url = 'https:' + m3u8_url
        elif m3u8_url.startswith('/'):
            m3u8_url = 'https://' + self.base_domain + m3u8_url
        elif not m3u8_url.startswith('http'):
            # Try to construct full URL
            m3u8_url = 'https://' + self.base_domain + '/' + m3u8_url.lstrip('/')
        
        return m3u8_url
    
    # ==================== EPISODE INFO ====================
    def extract_episode_info(self, soup):
        """Extract episode title and info (for UI only)"""
        try:
            # Multiple selectors for title
            title_selectors = [
                'h1.entry-title',
                'h1.title',
                'h1',
                '.episode-title',
                '.video-title',
                '.post-title',
                'title'
            ]
            
            title = "Unknown Episode"
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    title = element.text.strip()
                    break
            
            # Clean title
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove after |
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Extract episode number
            episode_num = "01"
            ep_match = re.search(r'Episode\s*(\d+)', title, re.IGNORECASE)
            if not ep_match:
                ep_match = re.search(r'EP\s*(\d+)', title, re.IGNORECASE)
            if not ep_match:
                ep_match = re.search(r'#(\d+)', title)
            
            if ep_match:
                episode_num = ep_match.group(1).zfill(2)
            
            # Clean filename
            cleaned = self.clean_filename(title)
            
            return {
                "title": title,
                "cleaned_title": cleaned,
                "episode_number": episode_num
            }
        except:
            return {
                "title": "Episode",
                "cleaned_title": "episode",
                "episode_number": "01"
            }
    
    def clean_filename(self, text):
        """Create safe text for filename"""
        if not text:
            return "episode"
        
        # Remove invalid characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-.,!&]', '', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Trim and limit length
        return text.strip()[:80]
