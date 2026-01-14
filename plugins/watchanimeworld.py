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
        """Hybrid scraper: Try both methods"""
        try:
            # 1️⃣ First try: ZephyrFlick iframe method (for current site)
            result = await self.scrape_zephyrflick(url)
            if result and "error" not in result:
                return result
            
            # 2️⃣ Second try: Meido-style AJAX method (if site changes)
            result = await self.scrape_ajax_method(url)
            if result and "error" not in result:
                return result
            
            # If both fail
            return {"error": "No video source found using any method"}
            
        except Exception as e:
            return {"error": f"Scraping failed: {str(e)}"}
    
    # ==================== ZEPHYRFLICK METHOD ====================
    async def scrape_zephyrflick(self, url):
        """Extract from ZephyrFlick iframe player"""
        try:
            # 1. Fetch episode page
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 2. Find ZephyrFlick iframe
            zephyr_iframe = None
            iframes = soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'zephyrflick' in src.lower():
                    zephyr_iframe = src
                    break
            
            if not zephyr_iframe:
                # Try alternative player iframe
                for iframe in iframes:
                    src = iframe.get('src', '')
                    if src and 'video' in src.lower():
                        zephyr_iframe = src
                        break
            
            if not zephyr_iframe:
                return {"error": "No player iframe found"}
            
            # 3. Fix iframe URL if needed
            if zephyr_iframe.startswith('//'):
                zephyr_iframe = f"https:{zephyr_iframe}"
            
            # 4. Fetch ZephyrFlick player page
            player_headers = {
                'User-Agent': USER_AGENT,
                'Referer': url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            player_html = await fetch_url(self.session, zephyr_iframe, player_headers)
            if not player_html:
                return {"error": "Failed to fetch player page"}
            
            player_soup = BeautifulSoup(player_html, 'lxml')
            
            # 5. Extract video sources from ZephyrFlick
            video_data = await self.extract_from_zephyrflick(player_soup, zephyr_iframe)
            if "error" in video_data:
                return video_data
            
            # 6. Extract episode info
            episode_info = self.extract_episode_info(soup)
            
            # ✅ SUCCESS
            return {
                "success": True,
                "episode_info": episode_info,
                "player_data": video_data,
                "source_url": url,
                "method": "zephyrflick_iframe"
            }
            
        except Exception as e:
            return {"error": f"ZephyrFlick method failed: {str(e)}"}
    
    async def extract_from_zephyrflick(self, soup, referer_url):
        """Extract video URL from ZephyrFlick player"""
        try:
            # Method 1: Check for video.js player
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Pattern 1: videojs setup with sources
                if 'videojs(' in script_text or 'player(' in script_text:
                    # Look for sources array
                    sources_patterns = [
                        r'sources\s*:\s*\[(.*?)\]',
                        r'"sources"\s*:\s*\[(.*?)\]',
                    ]
                    
                    for pattern in sources_patterns:
                        match = re.search(pattern, script_text, re.DOTALL)
                        if match:
                            sources_text = match.group(1)
                            # Extract URLs from sources
                            url_pattern = r'["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']'
                            urls = re.findall(url_pattern, sources_text)
                            if urls:
                                return {
                                    "type": "m3u8" if '.m3u8' in urls[0].lower() else "mp4",
                                    "url": urls[0],
                                    "referer": referer_url,
                                    "quality": "auto"
                                }
                
                # Pattern 2: Direct m3u8 URL
                m3u8_patterns = [
                    r'(https?://[^"\']+\.m3u8[^"\']*)',
                    r'file\s*[:=]\s*["\'](https?://[^"\']+\.m3u8)["\']',
                    r'src\s*[:=]\s*["\'](https?://[^"\']+\.m3u8)["\']',
                ]
                
                for pattern in m3u8_patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        url = match if isinstance(match, str) else match[0]
                        if url and '.m3u8' in url.lower():
                            return {
                                "type": "m3u8",
                                "url": url,
                                "referer": referer_url,
                                "quality": "auto"
                            }
            
            # Method 2: Check for JW Player
            for script in scripts:
                if not script.string:
                    continue
                
                if 'jwplayer(' in script.string:
                    # Extract JW Player setup
                    jw_pattern = r'jwplayer\([^)]+\)\.setup\((\{.*?\})\);'
                    match = re.search(jw_pattern, script.string, re.DOTALL)
                    if match:
                        try:
                            player_config = json.loads(match.group(1))
                            if 'sources' in player_config and player_config['sources']:
                                for source in player_config['sources']:
                                    if 'file' in source:
                                        url = source['file']
                                        return {
                                            "type": "m3u8" if '.m3u8' in url.lower() else "mp4",
                                            "url": url,
                                            "referer": referer_url,
                                            "quality": source.get('label', 'auto')
                                        }
                        except:
                            pass
            
            # Method 3: Look for video tag
            video_tags = soup.find_all('video')
            for video in video_tags:
                # Check source tags
                source_tags = video.find_all('source')
                for source in source_tags:
                    src = source.get('src')
                    if src:
                        return {
                            "type": "m3u8" if '.m3u8' in src.lower() else "mp4",
                            "url": src,
                            "referer": referer_url,
                            "quality": source.get('label', 'auto')
                        }
                
                # Check video src directly
                if video.get('src'):
                    src = video['src']
                    return {
                        "type": "m3u8" if '.m3u8' in src.lower() else "mp4",
                        "url": src,
                        "referer": referer_url,
                        "quality": "auto"
                    }
            
            return {"error": "No video source found in ZephyrFlick player"}
            
        except Exception as e:
            return {"error": f"ZephyrFlick extraction failed: {str(e)}"}
    
    # ==================== AJAX METHOD (KEEP AS BACKUP) ====================
    async def scrape_ajax_method(self, url):
        """Meido-style AJAX method (backup)"""
        try:
            html = await fetch_url(self.session, url)
            if not html:
                return {"error": "Failed to fetch episode page"}
            
            # Extract episode ID
            episode_id = self.extract_episode_id(html)
            if not episode_id:
                return {"error": "Could not extract episode ID"}
            
            # Try AJAX request
            ajax_response = await self.fetch_player_ajax(episode_id, url)
            if not ajax_response:
                return {"error": "AJAX request failed"}
            
            # Extract m3u8
            m3u8_url = self.extract_m3u8_from_ajax(ajax_response)
            if not m3u8_url:
                return {"error": "No m3u8 in AJAX response"}
            
            # Fix URL
            m3u8_url = self.fix_m3u8_url(m3u8_url)
            
            # Episode info
            soup = BeautifulSoup(html, 'lxml')
            episode_info = self.extract_episode_info(soup)
            
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
                "method": "ajax"
            }
            
        except Exception as e:
            return {"error": f"AJAX method failed: {str(e)}"}
    
    def extract_episode_id(self, html):
        """Extract episode ID from HTML"""
        patterns = [
            r'data-post=["\'](\d+)["\']',
            r'data-id=["\'](\d+)["\']',
            r'episode_id\s*[=:]\s*["\']?(\d+)["\']?',
            r'post_id\s*[=:]\s*["\']?(\d+)["\']?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    async def fetch_player_ajax(self, episode_id, referer_url):
        """Fetch player data via AJAX"""
        ajax_url = f"https://{self.base_domain}/wp-admin/admin-ajax.php"
        
        actions = [
            "player_ajax", "get_player", "load_player", 
            "episode_player", "anime_player"
        ]
        
        headers = {
            "User-Agent": USER_AGENT,
            "Referer": referer_url,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        for action in actions:
            try:
                data = {"action": action, "episode_id": episode_id}
                
                async with self.session.post(
                    ajax_url, data=data, headers=headers, timeout=10
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        if text and text.strip():
                            return text
            except:
                continue
        
        return None
    
    def extract_m3u8_from_ajax(self, response_text):
        """Extract m3u8 from AJAX response"""
        patterns = [
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
            r'["\'](//[^"\']+\.m3u8)["\']',
            r'file\s*[=:]\s*["\']([^"\']+\.m3u8)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                url = match if isinstance(match, str) else match[0]
                if url:
                    return url
        
        # Try JSON
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                if data.get("file") and ".m3u8" in data["file"].lower():
                    return data["file"]
                if data.get("sources"):
                    for source in data["sources"]:
                        if source.get("file") and ".m3u8" in source["file"].lower():
                            return source["file"]
        except:
            pass
        
        return None
    
    def fix_m3u8_url(self, m3u8_url):
        """Fix URL format"""
        if not m3u8_url:
            return m3u8_url
        
        if m3u8_url.startswith('//'):
            m3u8_url = 'https:' + m3u8_url
        elif m3u8_url.startswith('/'):
            m3u8_url = 'https://' + self.base_domain + m3u8_url
        
        return m3u8_url
    
    # ==================== EPISODE INFO ====================
    def extract_episode_info(self, soup):
        """Extract episode title and info"""
        try:
            title_selectors = [
                'h1.entry-title', 'h1.title', 'h1',
                '.episode-title', '.video-title', 'title'
            ]
            
            title = "Unknown Episode"
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element and element.text.strip():
                    title = element.text.strip()
                    break
            
            # Clean title
            title = re.sub(r'\s*\|\s*.*$', '', title)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Episode number
            episode_num = "01"
            ep_match = re.search(r'Episode\s*(\d+)', title, re.IGNORECASE)
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
        """Create safe filename"""
        if not text:
            return "episode"
        
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        text = re.sub(r'[^\w\s\-.,!&]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:80]
